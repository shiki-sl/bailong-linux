"""Independent Codex cost/throughput collection using the bundled Tokscale CLI.

No GUI/archive/settings from Token Monitor are needed. Unknown model identities
are excluded from cost, and rates only use counters with full timing coverage.
"""
import datetime as dt
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]


def number(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 else 0.


def summarize(payload, priced_models, checked=None):
    entries = payload.get('entries')
    if not isinstance(entries, list):
        raise ValueError('Missing usage entries')
    result = dict(day=dt.date.today().isoformat(), checked=checked or time.time(),
                  cost_usd=0., total_tokens=0, unpriced_tokens=0, unpriced_models=[],
                  models={}, throughput={}, source='Tokscale 4.18.0 · 本机 Codex')
    for row in entries:
        if not isinstance(row, dict) or row.get('client') != 'codex':
            raise ValueError('Unexpected usage client')
        model = str(row.get('model') or 'unknown')
        # Tokscale emits disjoint visible-output and reasoning buckets. Codex's
        # original output_tokens already includes reasoning; restore it once.
        output = number(row.get('output')) + number(row.get('reasoning'))
        tokens = sum(number(row.get(key)) for key in ('input', 'cacheRead', 'cacheWrite')) + output
        result['total_tokens'] += tokens
        cost = row.get('cost')
        missing = number(row.get('unpricedTokens'))
        priced = model in priced_models and isinstance(cost, (int, float)) and math.isfinite(cost) and cost >= 0 and not missing
        if priced:
            result['cost_usd'] += cost
        else:
            result['unpriced_tokens'] += tokens
            if tokens and model not in result['unpriced_models']:
                result['unpriced_models'].append(model)
        result['models'][model] = dict(tokens=tokens, cost_usd=cost if priced else None)
        perf = row.get('performance') or {}
        duration = number(perf.get('totalDurationMs'))
        # Without matched output timing we cannot multiply output by coverage.
        if duration > 0 and perf.get('tokenCoverage') == 1:
            result['throughput'][model] = dict(output=output,
                                               tokens=number(perf.get('timedTokens')), duration=duration)
    return result


class RateTracker:
    def __init__(self):
        self.previous = None
        self.recent = None

    def update(self, snapshot):
        previous = self.previous
        current = snapshot.get('throughput', {})
        if previous and previous['day'] == snapshot['day']:
            before = previous.get('throughput', {})
            # A disappearing model or regressed counter invalidates the baseline.
            reset = any(model not in current or any(current[model][k] < values[k] for k in values)
                        for model, values in before.items())
            if reset:
                self.recent = None
            else:
                delta = dict(output=0., tokens=0., duration=0.)
                for model, values in current.items():
                    # A newly timed model starts a baseline, never a historical burst.
                    if model not in before:
                        continue
                    change = {k: values[k] - before[model][k] for k in values}
                    if change['duration'] > 0:
                        for key in delta:
                            delta[key] += change[key]
                if delta['duration'] > 0:
                    self.recent = dict(output_tps=delta['output'] * 1000 / delta['duration'],
                                       burn_tpm=delta['tokens'] * 60000 / delta['duration'],
                                       at=snapshot['checked'])
        else:
            self.recent = None
        self.previous = snapshot
        total = {k: sum(v[k] for v in current.values()) for k in ('output', 'tokens', 'duration')}
        snapshot['average_tps'] = total['output'] * 1000 / total['duration'] if total['duration'] else None
        snapshot['recent'] = self.recent
        return snapshot


class Collector:
    def __init__(self, state, stop=lambda: False, vendor=None, codex_home=None):
        self.vendor = Path(vendor or ROOT / 'vendor/tokscale')
        self.config = Path(state) / 'metrics-collector'
        self.config.mkdir(parents=True, exist_ok=True)
        cache = self.config / 'cache'
        cache.mkdir(exist_ok=True)
        for source in (self.vendor / 'cache').glob('pricing-*.json'):
            target = cache / source.name
            if not target.exists():
                shutil.copy2(source, target)
        self.stop = stop
        self.codex_home = codex_home
        self.prices = {}
        self.tracker = RateTracker()

    def command(self, args):
        env = dict(os.environ, TOKSCALE_CONFIG_DIR=str(self.config))
        # Do not inherit optional multi-client scan expansions from another tool.
        env.pop('TOKSCALE_EXTRA_DIRS', None)
        env.pop('TOKSCALE_HEADLESS_DIR', None)
        if self.codex_home:
            env['CODEX_HOME'] = str(self.codex_home)
        process = subprocess.Popen([str(self.vendor / 'tokscale'), *args, '--no-spinner'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        deadline = time.monotonic() + 20
        try:
            while True:
                if self.stop() or time.monotonic() >= deadline:
                    raise RuntimeError('Collector stopped or timed out')
                try:
                    stdout, _stderr = process.communicate(timeout=.25)
                    break
                except subprocess.TimeoutExpired:
                    pass
            if process.returncode:
                raise RuntimeError('Collector failed')
            return json.loads(stdout)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()

    def poll(self):
        day = dt.date.today().isoformat()
        payload = self.command(['--json', '--client', 'codex', '--today'])
        models = {row['model'] for row in payload.get('entries', [])}
        for model in models:
            cached = self.prices.get(model)
            if cached and time.monotonic() - cached[0] < 3600:
                continue
            price = self.command(['pricing', model, '--json'])
            safe = price.get('resolution', {}).get('exactModelIdentity') is True
            self.prices[model] = (time.monotonic(), safe)
        if day != dt.date.today().isoformat():
            raise RuntimeError('Day changed during collection')
        priced = {model for model, (_, safe) in self.prices.items() if safe}
        return self.tracker.update(summarize(payload, priced))


def presentation(snapshot, now=None):
    now = time.time() if now is None else now
    if not snapshot or snapshot.get('day') != dt.datetime.fromtimestamp(now).date().isoformat():
        failed = snapshot and snapshot.get('error')
        return dict(cost='—', rate='—', rate_title='输出速率',
                    note='采集失败 · 等待重试' if failed else '等待今日采样', tooltip='只统计本机可读的 Codex 日志。')
    stale = now - snapshot['checked'] > 90 or snapshot.get('error', False)
    missing = snapshot.get('unpriced_tokens', 0)
    priced = snapshot.get('total_tokens', 0) - missing
    cost = f"≈${snapshot['cost_usd']:.2f}" if priced > 0 or not missing else '—'
    if missing and priced > 0:
        cost += '*'
    recent = snapshot.get('recent')
    active = not stale and recent and now - recent['at'] <= 180
    rate = recent['output_tps'] if active else snapshot.get('average_tps')
    title = '近期均速' if active else '今日均速'
    stamp = time.strftime('%H:%M:%S', time.localtime(snapshot['checked']))
    note = ('更新失败 · ' if stale else '') + stamp + (' · 部分未计价' if missing else ' · 本机 Codex')
    details = ['本机 Codex，所有可读模型；每 10 秒采样一次。',
               '金额：采集器按 API 价格估算，区分缓存输入；不是订阅账单或账户额度。',
               '可能无法还原服务档位、工具等费用；不保证与实际收费一致。',
               f'最近成功采样：{stamp}' + ('；数据已过期或更新失败。' if stale else '。'),
               '输出速率：有完整计时的输出 Token（含推理）÷ 对应请求耗时；多请求取加权平均。',
               '“近期”使用两次采样的增量；没有新计时样本时显示今日平均，不代表瞬时速度。']
    if missing:
        details.append(f'未计价 {missing:,.0f} Token：' + '、'.join(snapshot.get('unpriced_models', [])))
    for model, values in sorted(snapshot.get('models', {}).items()):
        amount = '未计价' if values['cost_usd'] is None else f"≈${values['cost_usd']:.4f}"
        details.append(f'{model}：{amount} / {values["tokens"]:,.0f} Token')
    if active:
        details.append(f'近期总 Token 耗速（含输入缓存）：{recent["burn_tpm"]:,.0f} tok/min')
    return dict(cost=cost, rate=f'{rate:.1f} tok/s' if rate is not None else '—',
                rate_title=title, note=note, tooltip='\n'.join(details))
