import logging

logger = logging.getLogger(__name__)

# Exact 9-class normalized literature baseline priors (Sum = 1.00)
LITERATURE_PRIORS = {
    "mahali_koleroga": 0.30,
    "yellow_leaf_disease": 0.20,
    "stem_bleeding": 0.08,
    "stem_cracking": 0.08,
    "bud_borer": 0.08,
    "healthy_nut": 0.08,
    "healthy_leaf": 0.08,
    "healthy_trunk": 0.06,
    "healthy_foot": 0.04,
}

VALIDATION_THRESHOLD = 0.75  # Threshold > 0.75 per Major_Final_!.md §4.4.2


def get_hybrid_prior(predicted_disease: str, historical_detections: list, pseudo_count: float = 5.0) -> float:
    """
    Computes hybrid prior P(Disease):
    - When regional detections count N < 10, uses the literature baseline prior P0.
    - When N >= 10, uses Laplace/m-estimate smoothed empirical frequency: (count + m*P0) / (N + m).
    """
    p0 = LITERATURE_PRIORS.get(predicted_disease, 0.10)
    total_n = len(historical_detections)

    if total_n < 10:
        return p0

    disease_matches = sum(1 for d in historical_detections if d.predicted_disease == predicted_disease)
    smoothed_prior = (disease_matches + pseudo_count * p0) / (total_n + pseudo_count)
    return round(float(smoothed_prior), 4)


def compute_posterior(
    cnn_confidence: float,
    weather_risk_score: float,
    predicted_disease: str,
    historical_prior: float,
    is_synthetic_weather: bool = False,
) -> tuple[float, bool]:
    """
    Computes Bayesian Posterior Probability P(Disease | Image, Weather, History)
    P(D | Evidence) = [P(Image|D) * P(Weather|D) * P(D)] / P(Evidence)

    Where P(Evidence) is normalized across binary hypothesis states:
    P(Evidence) = P(Image|D)*P(Weather|D)*P(D) + P(Image|¬D)*P(Weather|¬D)*P(¬D)

    Returns:
        tuple (posterior_probability: float, validated: bool)
    """
    # 1. Image Likelihoods
    p_image_given_d = max(0.01, min(0.99, float(cnn_confidence)))
    p_image_given_not_d = 1.0 - p_image_given_d

    # 2. Weather Likelihoods (scaled from 0-100 risk score)
    norm_score = max(0.0, min(100.0, float(weather_risk_score))) / 100.0
    is_healthy = predicted_disease.startswith("healthy_")

    if is_healthy:
        # Dry/unfavorable disease conditions favor healthy palm observations
        p_weather_given_d = 0.95 - (norm_score * 0.75)
        p_weather_given_not_d = 0.20 + (norm_score * 0.75)
    else:
        # High humidity & rainfall heavily favor fungal disease occurrence
        p_weather_given_d = 0.20 + (norm_score * 0.75)
        p_weather_given_not_d = 0.95 - (norm_score * 0.75)

    # 3. Synthetic Weather Dampening (shrink toward uninformative neutral likelihood 0.50)
    if is_synthetic_weather:
        p_weather_given_d = 0.50 + 0.50 * (p_weather_given_d - 0.50)
        p_weather_given_not_d = 0.50 + 0.50 * (p_weather_given_not_d - 0.50)

    # 4. Prior Probabilities
    p_d = max(0.01, min(0.99, float(historical_prior)))
    p_not_d = 1.0 - p_d

    # 5. Marginal Evidence Normalization
    joint_d = p_image_given_d * p_weather_given_d * p_d
    joint_not_d = p_image_given_not_d * p_weather_given_not_d * p_not_d

    marginal_evidence = joint_d + joint_not_d
    if marginal_evidence <= 0:
        posterior = p_image_given_d
    else:
        posterior = joint_d / marginal_evidence

    posterior = round(float(min(0.9999, max(0.0001, posterior))), 4)
    validated = bool(posterior > VALIDATION_THRESHOLD)

    return posterior, validated
