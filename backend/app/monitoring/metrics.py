"""Monitoring metrics and alerts."""

from datetime import datetime
from typing import Dict, Any, List
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class AlertRule:
    """Alert rule for monitoring."""

    def __init__(self, name: str, metric: str, threshold: float, operator: str):
        self.name = name
        self.metric = metric  # 'error_rate', 'latency', 'cache_hit_rate', 'qps'
        self.threshold = threshold
        self.operator = operator  # '<', '>', '<=', '>='
        self.is_triggered = False
        self.triggered_at = None

    def check(self, value: float) -> bool:
        """Check if alert should trigger."""
        if self.operator == '>':
            triggered = value > self.threshold
        elif self.operator == '>=':
            triggered = value >= self.threshold
        elif self.operator == '<':
            triggered = value < self.threshold
        elif self.operator == '<=':
            triggered = value <= self.threshold
        else:
            triggered = False

        if triggered and not self.is_triggered:
            self.is_triggered = True
            self.triggered_at = datetime.utcnow()
            logger.warning(f"ALERT: {self.name} - {self.metric}={value} (threshold={self.threshold})")

        elif not triggered and self.is_triggered:
            self.is_triggered = False
            logger.info(f"RESOLVED: {self.name}")

        return triggered


class MonitoringSystem:
    """System monitoring and alerting."""

    def __init__(self):
        self.metrics_history: Dict[str, List[float]] = defaultdict(list)
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: List[AlertRule] = []
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Setup default alert rules."""
        self.alert_rules = [
            AlertRule("High Error Rate", "error_rate", 0.05, ">"),  # > 5%
            AlertRule("High Latency", "latency", 5000, ">"),  # > 5 seconds
            AlertRule("Low Cache Hit Rate", "cache_hit_rate", 0.3, "<"),  # < 30%
            AlertRule("High QPS", "qps", 100, ">"),  # > 100 queries/sec
        ]

    def record_metric(self, metric_name: str, value: float):
        """Record a metric value."""
        self.metrics_history[metric_name].append(value)
        # Keep only last 1000 values
        if len(self.metrics_history[metric_name]) > 1000:
            self.metrics_history[metric_name] = self.metrics_history[metric_name][-1000:]

    def check_alerts(self, current_metrics: Dict[str, float]):
        """Check all alert rules."""
        self.active_alerts = []
        for rule in self.alert_rules:
            if rule.metric in current_metrics:
                if rule.check(current_metrics[rule.metric]):
                    self.active_alerts.append(rule)

    def get_alert_status(self) -> Dict[str, Any]:
        """Get alert status."""
        return {
            'total_rules': len(self.alert_rules),
            'active_alerts': len(self.active_alerts),
            'triggered_alerts': [
                {
                    'name': rule.name,
                    'metric': rule.metric,
                    'threshold': rule.threshold,
                    'triggered_at': rule.triggered_at.isoformat() if rule.triggered_at else None,
                }
                for rule in self.active_alerts
            ],
        }

    def get_health_status(self, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Get overall system health status."""
        self.check_alerts(current_metrics)

        # Calculate health score
        health_score = 100
        if current_metrics.get('error_rate', 0) > 0.05:
            health_score -= 20
        if current_metrics.get('latency', 0) > 5000:
            health_score -= 15
        if current_metrics.get('cache_hit_rate', 0) < 0.3:
            health_score -= 10
        if len(self.active_alerts) > 0:
            health_score -= 10 * len(self.active_alerts)

        health_score = max(0, min(100, health_score))

        return {
            'health_score': health_score,
            'status': 'Healthy' if health_score >= 80 else 'Degraded' if health_score >= 60 else 'Critical',
            'active_alerts': len(self.active_alerts),
            'metrics': current_metrics,
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        summary = {}
        for metric_name, values in self.metrics_history.items():
            if values:
                summary[metric_name] = {
                    'current': values[-1],
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                }

        return summary


# Global instance
monitoring_system = MonitoringSystem()
