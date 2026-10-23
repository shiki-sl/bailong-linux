"""Cost coverage and timing regressions for the Linux metrics integration."""
import datetime as dt
import unittest
from usage_metrics import summarize, RateTracker, presentation


def row(model='known', output=10, duration=2000, coverage=1, cost=.005):
    return dict(client='codex', model=model, input=20, cacheRead=80, output=output,
                cost=cost, performance=dict(totalDurationMs=duration,
                                           timedTokens=100+output, tokenCoverage=coverage))


class UsageMetricsTests(unittest.TestCase):
    def test_fuzzy_price_is_excluded_and_cached_input_is_counted_once(self):
        known = row(output=7)
        known['reasoning'] = 3
        value = summarize(dict(entries=[known, row('codex-auto-review', cost=900)]), {'known'})
        self.assertEqual(value['cost_usd'], .005)
        self.assertEqual(value['total_tokens'], 220)
        self.assertEqual(value['unpriced_tokens'], 110)
        self.assertEqual(value['unpriced_models'], ['codex-auto-review'])
        self.assertEqual(value['throughput']['known']['output'], 10)
        text = presentation(value)
        self.assertTrue(text['cost'].endswith('*'))
        self.assertIn('codex-auto-review', text['tooltip'])

    def test_rate_uses_matched_duration_not_ten_second_poll_interval(self):
        tracker = RateTracker()
        first = tracker.update(summarize(dict(entries=[row()]), {'known'}, checked=100))
        self.assertEqual(first['average_tps'], 5)
        second = tracker.update(summarize(dict(entries=[row(output=30, duration=3000)]), {'known'}, checked=110))
        self.assertEqual(second['recent']['output_tps'], 20)
        self.assertIsNone(tracker.update(summarize(dict(entries=[row()]), {'known'}, checked=120))['recent'])

    def test_incomplete_timing_never_extrapolates_output_and_new_model_is_baseline(self):
        tracker = RateTracker()
        first = tracker.update(summarize(dict(entries=[row(coverage=.5)]), {'known'}))
        self.assertIsNone(first['average_tps'])
        second = tracker.update(summarize(dict(entries=[row()]), {'known'}))
        self.assertIsNone(second['recent'])
        self.assertEqual(second['average_tps'], 5)

    def test_stale_failure_and_midnight_are_visible(self):
        now = dt.datetime.now().timestamp()
        value = RateTracker().update(summarize(dict(entries=[row()]), {'known'}, checked=now))
        value['recent'] = dict(at=now, output_tps=42, burn_tpm=100)
        self.assertEqual(presentation(value, now)['rate_title'], '近期均速')
        self.assertEqual(presentation(value, now+181)['rate_title'], '今日均速')
        value['error'] = True
        self.assertIn('更新失败', presentation(value, now)['note'])
        value['day'] = (dt.date.today()-dt.timedelta(days=1)).isoformat()
        self.assertEqual(presentation(value, now)['cost'], '—')


if __name__ == '__main__':
    unittest.main()
