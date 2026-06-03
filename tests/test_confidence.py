import pytest
from backend.app.generation.confidence import ConfidenceScorer, ConfidenceMetrics


@pytest.fixture
def scorer():
    """Confidence scorer instance."""
    return ConfidenceScorer()


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing."""
    return [
        {
            "text": "To restart a pod in Kubernetes, use kubectl rollout restart deployment/my-app",
            "source": "kubernetes-guide.pdf",
            "metadata": {"section": "Pod Management", "page": 42},
        },
        {
            "text": "ImagePullBackOff error occurs when the container image cannot be pulled",
            "source": "kubernetes-errors.pdf",
            "metadata": {"section": "Errors", "page": 78},
        },
    ]


def test_confidence_scorer_initialization(scorer):
    """Test scorer initializes correctly."""
    assert scorer is not None
    assert scorer.uncertainty_pattern is not None
    assert scorer.confidence_pattern is not None


def test_high_confidence_response(scorer, sample_chunks):
    """Test high-confidence response scoring."""
    response = (
        "According to the kubernetes-guide.pdf, to restart a pod, "
        "you use the kubectl rollout restart command. "
        "Based on the documentation, this is the recommended approach."
    )
    query = "how to restart a pod"

    metrics = scorer.score(response, sample_chunks, query)

    assert metrics.overall_confidence > 0.7
    assert metrics.source_coverage > 0.5
    assert metrics.hallucination_risk < 0.3
    assert metrics.uncertainty_markers < 3


def test_low_confidence_response(scorer, sample_chunks):
    """Test low-confidence response with uncertainty markers."""
    response = (
        "I think maybe you could possibly try something like kubectl rollout restart, "
        "but I'm not really sure if that would work. It might help, but I'm uncertain."
    )
    query = "how to restart a pod"

    metrics = scorer.score(response, sample_chunks, query)

    assert metrics.overall_confidence < 0.6
    assert metrics.uncertainty_markers > 2


def test_fallback_response(scorer, sample_chunks):
    """Test fallback response (no hallucination risk)."""
    response = "I don't have reliable information to answer this question. Please consult the documentation or contact support."
    query = "something not in sources"

    metrics = scorer.score(response, sample_chunks, query)

    assert metrics.hallucination_risk == 0.0


def test_source_coverage_scoring(scorer, sample_chunks):
    """Test source coverage scoring."""
    # Good coverage - mentions both sources
    response_good = (
        "According to kubernetes-guide.pdf and kubernetes-errors.pdf, "
        "here's what you need to know."
    )

    metrics_good = scorer.score(response_good, sample_chunks, "test")
    assert metrics_good.source_coverage > 0.5

    # Poor coverage - mentions no sources
    response_poor = "Here's some information about Kubernetes."
    metrics_poor = scorer.score(response_poor, sample_chunks, "test")
    assert metrics_poor.source_coverage < 0.5


def test_hallucination_risk_scoring(scorer, sample_chunks):
    """Test hallucination risk detection."""
    # Response with unfounded claim
    response = (
        "You should use kubectl delete pod to restart it. "
        "This is a secret command not documented anywhere."
    )

    metrics = scorer.score(response, sample_chunks, "how to restart")
    assert metrics.hallucination_risk > 0.2


def test_completeness_scoring(scorer, sample_chunks):
    """Test answer completeness scoring."""
    # Short, incomplete response
    response_short = "Use kubectl rollout."
    metrics_short = scorer.score(response_short, sample_chunks, "how to restart a pod")
    assert metrics_short.answer_completeness < 0.5

    # Detailed, complete response
    response_long = (
        "To restart a pod in Kubernetes, you should use the kubectl rollout restart command "
        "followed by the deployment name. For example, kubectl rollout restart deployment/my-app. "
        "This will gracefully restart all pods managed by that deployment, causing them to be "
        "recreated with new containers. You can also monitor the rollout status with kubectl."
    )
    metrics_long = scorer.score(response_long, sample_chunks, "how to restart a pod")
    assert metrics_long.answer_completeness > 0.6


def test_uncertainty_markers_counting(scorer):
    """Test counting of uncertainty markers."""
    response_uncertain = (
        "I think you might possibly want to maybe try this approach. "
        "I'm not sure if it will work, but I believe you could try it."
    )

    count = scorer._count_uncertainty_markers(response_uncertain)
    assert count > 3

    response_certain = (
        "This is definitely the correct approach. Use kubectl rollout restart deployment/my-app."
    )
    count_certain = scorer._count_uncertainty_markers(response_certain)
    assert count_certain < response_uncertain.count("might")


def test_confidence_level_classification(scorer):
    """Test confidence level classification."""
    assert scorer.confidence_level(0.90) == "high"
    assert scorer.confidence_level(0.75) == "medium"
    assert scorer.confidence_level(0.50) == "low"
    assert scorer.confidence_level(0.30) == "very_low"


def test_technical_claims_extraction(scorer):
    """Test extraction of technical claims."""
    response = (
        "Use the command `kubectl rollout restart deployment/my-app`. "
        "Run: kubectl get pods to check status."
    )

    claims = scorer._extract_technical_claims(response)
    assert len(claims) > 0
    assert any("kubectl" in claim for claim in claims)


def test_confidence_metrics_structure(scorer, sample_chunks):
    """Test returned confidence metrics structure."""
    response = "Test response based on kubernetes-guide.pdf"
    query = "test query"

    metrics = scorer.score(response, sample_chunks, query)

    assert isinstance(metrics, ConfidenceMetrics)
    assert 0 <= metrics.source_coverage <= 1
    assert 0 <= metrics.hallucination_risk <= 1
    assert 0 <= metrics.answer_completeness <= 1
    assert 0 <= metrics.overall_confidence <= 1
    assert metrics.uncertainty_markers >= 0


def test_empty_response(scorer, sample_chunks):
    """Test scoring empty response."""
    response = ""
    metrics = scorer.score(response, sample_chunks, "test")

    assert metrics.answer_completeness < 0.5
    assert metrics.overall_confidence < 0.5


def test_empty_chunks(scorer):
    """Test scoring with empty chunks."""
    response = "Some response"
    metrics = scorer.score(response, [], "test")

    assert metrics.source_coverage == 0.0
