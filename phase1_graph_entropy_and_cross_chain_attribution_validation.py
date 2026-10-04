# Intended validation: Run all six Phase 1 mathematical validation suites.
# Validate event graphs and flow tensors; peeling-chain entropy and allocation;
# bridge correlation and AMM identities; metrics and equivalence relations;
# attribution reliability; and custodial entity projection.
# Preserve every original fixture, counterexample, seed, and finding.
# These synthetic checks distinguish supported, contradicted, and unspecified
# claims. Successful execution means the checks ran, not that every claim holds.
#
# Title: Phase 1 Graph Entropy and Cross Chain Attribution Validation
# Requirements: Python 3.9+, NumPy, SciPy
# Install: python -m pip install numpy scipy
# Run: python phase1_graph_entropy_and_cross_chain_attribution_validation.py
# Save JSON: add --output phase1_results.json
# No other Phase 1 files are needed to run this script.

# MIT License
# Copyright (c) September 2026 Roger Cooperman; A.E. Petrunina V.V.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import argparse
import json
import math
import platform
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import beta, binom, chi2, norm

SEED = 20260901


def require(condition, label):
    """Check fixture implementation, not the truth of every manuscript claim."""
    if not condition:
        raise AssertionError(label)


# Intended validation: Proposition 1.1 and Definitions 1.1.1–1.1.3.
# Check event-level acyclicity, equal timestamps, asynchronous chain ordering,
# per-asset conservation, tensor aggregation, time-bin endpoints, and the
# orientation, units, and information retained by the transition operator.
# All examples are synthetic; a passing example does not prove universality.


def acyclic(edges):
    nodes = set(v for edge in edges for v in edge)
    successors = {v: [] for v in nodes}
    indegree = dict.fromkeys(nodes, 0)
    for u, v in edges:
        successors[u].append(v)
        indegree[v] += 1
    ready = [v for v in nodes if indegree[v] == 0]
    visited = 0
    while ready:
        u = ready.pop()
        visited += 1
        for v in successors[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                ready.append(v)
    return visited == len(nodes)


def validate_graph_and_tensor():
    """Return all original findings for graph and tensor."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    # Account reuse creates a cycle at address level, but not at event level.
    address_edges = [('A', 'B'), ('B', 'A')]
    event_edges = [('A0', 'B1'), ('B1', 'A2')]
    require(not acyclic(address_edges) and acyclic(event_edges), 'graph fixture')
    record('1.1 event DAG', 'supported under stated assumptions',
           'A strict causal rank on every edge gives a DAG; address aggregation can create cycles.',
           address_graph_acyclic=False, event_graph_acyclic=True)
    timestamps = {'A0': 100, 'B1': 100, 'A2': 101}
    strict = all(timestamps[v] > timestamps[u] for u, v in event_edges)
    require(not strict, 'equal-time fixture')
    record('1.1 timestamp proof', 'insufficiently specified',
           'Recorded timestamps need not be strictly increasing. Use causal order, transaction indices, and verified bridge dependencies.',
           strict_recorded_timestamp_order=strict,
           asynchronous_bridge_example={'source_time': 101, 'destination_time': 99,
                                        'causal_edge': 'source -> destination'})
    # Exact integer accounting: a retained balance must be an explicit output
    # or a stock-change term. Quantities of different assets cannot be summed.
    incoming, outgoing, fee, retained = 100, 60, 2, 38
    require(incoming - outgoing - fee - retained == 0, 'stock-flow conservation')
    record('1.1 conservation', 'contradicted',
           'The stated fee-only residual fails for a partially retained account balance unless a carry-forward edge is added.',
           paper_residual=incoming-outgoing-fee, corrected_residual=0,
           exchange_example={'asset_A_in': 100, 'asset_B_out': 2,
                             'warning': '98 is not a meaningful cross-asset fee'})
    # (source, destination, asset, time, amount, fee)
    events = [(0, 1, 0, 0.0, 7, 1), (0, 1, 0, 0.5, 3, 2),
              (1, 2, 1, 1.0, 4, 0), (1, 2, 1, 2.0, 5, 0)]
    tensor = np.zeros((3, 3, 2, 2), dtype=np.int64)
    excluded = []
    for i, j, asset, t, amount, f in events:
        if 0 <= t < 2:
            tensor[i, j, asset, int(t)] += amount
        else:
            excluded.append(t)
    require(tensor[0, 1, 0, 0] == 10 and tensor.sum() == 14, 'tensor sums')
    require(excluded == [2.0], 'half-open endpoint')
    record('1.1.2 aggregation', 'supported under stated assumptions',
           'Tensor entries reproduce per-asset, per-bin amount sums for a half-open observation interval.',
           tensor_total=int(tensor.sum()), excluded_endpoint=excluded)
    record('1.1.2 completeness', 'contradicted',
           'Two transfers of 7 and 3 with fees 1 and 2 have the same amount tensor as one transfer of 10 with any fee in that bin. Fees, exact times, and multiplicity are lost.')
    adjacency = tensor.sum(axis=(2, 3))
    source = np.array([1, 0, 0])
    paper = adjacency @ source
    forward = adjacency.T @ source
    require(paper.tolist() == [0, 0, 0] and forward.tolist() == [0, 10, 0], 'orientation')
    record('1.1.3 transition', 'contradicted',
           'For A[i,j] = flow i -> j, forwarding a column source indicator requires A.T. Amount-weighted A is not a balance transition matrix; assets also require separate units.',
           paper_result=paper.tolist(), forward_exposure=forward.tolist())
    return results


# Intended validation: Lemma 1.2 and Definitions 1.2.1–1.2.2.
# Verify the entropy–KL identity and allocation conservation; test fixed-point
# digit classification under uniform, fixed, and correlated fee models.
# Separate individual-output accuracy, whole-path accuracy, and repeated
# evidence about ONE common hypothesis. Treat ties as half-correct.


def digit_scores(values, precision=8):
    values = np.asarray(values, dtype=np.int64)
    digits = (values[:, None] // (10 ** np.arange(precision))) % 10
    probabilities = np.stack([(digits == s).mean(axis=1) for s in range(10)], axis=1)
    logs = np.zeros_like(probabilities)
    np.log(probabilities, out=logs, where=probabilities > 0)
    entropy = -(probabilities * logs).sum(axis=1)
    kl = (probabilities * (logs + math.log(10))).sum(axis=1)
    return entropy, kl


def validate_peeling_entropy():
    """Return all original findings for peeling entropy."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    rng = np.random.default_rng(SEED)
    n = 40000
    scale = 10**8
    values = rng.integers(0, scale, n)
    h, kl = digit_scores(values)
    residual = float(np.max(np.abs(kl - (math.log(10)-h))))
    require(residual < 1e-12, 'entropy identity')
    record('1.2 entropy identity', 'supported under stated assumptions',
           'Natural logarithms and 0 log 0 = 0 give KL(p||uniform) = log(10)-H(p).',
           max_absolute_residual=residual)
    lower_bound = math.log(10/8)
    require(float(kl.min()) >= lower_bound-1e-12, 'finite digit lower bound')
    record('1.2 fixed precision convergence', 'contradicted',
           'With eight digits, empirical digit entropy is at most log(8), so per-output KL is at least log(10/8), regardless of chain depth. Pooling digits across outputs is a different estimator.',
           exact_lower_bound=lower_bound, sampled_minimum=float(kl.min()),
           sampled_mean=float(kl.mean()))
    # A controlled favorable model: round peel; input a whole number of units;
    # uniformly distributed integer fee residues. This model is not a real fee fit.
    peel = np.full(n, scale, dtype=np.int64)
    fee = rng.integers(1, scale, n)
    change = 4*scale-peel-fee
    _, peel_kl = digit_scores(peel)
    _, change_kl = digit_scores(change)
    wins = int((change_kl < peel_kl-1e-12).sum())
    ties = int(np.isclose(change_kl, peel_kl, atol=1e-12, rtol=0).sum())
    accuracy = (wins+ties/2)/n
    lo = 0 if wins == 0 else float(beta.ppf(.025, wins, n-wins+1))
    hi = 1 if wins == n else float(beta.ppf(.975, wins+1, n-wins))
    # Both amounts end in eight zeros: a fixed fee creates persistent ambiguity.
    _, fixed_kl = digit_scores(np.array([scale, 2*scale]))
    require(np.isclose(fixed_kl[0], fixed_kl[1]), 'fixed-fee tie')
    # A deliberately non-round peel and round change invert the heuristic.
    _, inverted = digit_scores(np.array([12345678, 2*scale]))
    require(inverted[0] < inverted[1], 'inverted classifier')
    record('1.2 classifier models', 'insufficiently specified',
           'A favorable fee model works well; fixed fees can tie forever, and non-round payments can be selected incorrectly. Randomness or continuity alone does not imply uniform residues.',
           favorable_accuracy=accuracy, strict_wins=wins, ties=ties,
           strict_win_probability_95pct_interval=[lo, hi],
           fixed_fee_tie_accuracy=.5, inverted_example_correct=False)
    p = .8
    depths = [1, 5, 21, 101]
    rows = []
    for d in depths:
        rows.append({'depth': d, 'individual_accuracy': p,
                     'probability_all_steps_correct': p**d,
                     'independent_common_hypothesis_majority': float(binom.sf(d//2, d, p)),
                     'perfectly_correlated_majority': p})
    require(rows[-1]['probability_all_steps_correct'] < rows[0]['probability_all_steps_correct'], 'path accuracy')
    record('1.2 depth and likelihood', 'contradicted',
           'Fixed per-step accuracy does not converge to one with depth. Repeated independent observations of one common hypothesis can converge; different change outputs are different hypotheses.',
           examples=rows)
    vin = np.array([100., 50.])
    allocation = np.array([[.2, .6], [.8, .4]])
    vout = allocation @ vin - np.array([1., 1.])
    require(np.allclose(allocation.sum(axis=0), 1) and np.isclose(vout.sum(), vin.sum()-2), 'allocation')
    bad = np.array([[1., 1.], [0., 0.]]) @ vin - np.array([1., 1.])
    require(bad[1] < 0, 'negative output fixture')
    record('1.2.1 allocation', 'supported under stated assumptions',
           'Column sums of one conserve total quantity after fees; nonnegative allocations and sufficient row allocations to cover fees are additional feasibility requirements.',
           valid_outputs=vout.tolist(), infeasible_outputs=bad.tolist())
    features = np.array([[1., .1, 0., 0.], [0., .9, 1., 1.]])
    first = int(np.argmax(features @ np.array([1., 0., 0., 0.])))
    second = int(np.argmax(features @ np.array([0., 1., 0., 0.])))
    require(first != second, 'unspecified feature weights')
    record('1.2.2 projection', 'insufficiently specified',
           'Projection extracts a selected component, but weights, feature timing, and tie-breaking are unspecified. Future out-degree would introduce look-ahead if used at transaction time.',
           selections_under_two_weights=[first, second])
    return results


# Intended validation: Theorem 1.3.
# Verify the AMM rational formula with exact symbolic polynomial cancellation
# and Fraction arithmetic. Compare the claimed false-positive bound with exact
# chi-square probabilities, independent/correlated Gaussian simulations, and
# candidate multiplicity. Test the stated latency and centering assumptions.


def add(a, b):
    out = dict(a)
    for key, value in b.items():
        out[key] = out.get(key, 0) + value
    return {key: value for key, value in out.items() if value}


def mul(a, b):
    out = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            key = tuple(x+y for x, y in zip(ka, kb))
            out[key] = out.get(key, 0) + va*vb
    return {key: value for key, value in out.items() if value}


def interval(successes, trials):
    return [0. if successes == 0 else float(beta.ppf(.025, successes, trials-successes+1)),
            1. if successes == trials else float(beta.ppf(.975, successes+1, trials-successes))]


def validate_bridge_correlation():
    """Return all original findings for bridge correlation."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    # Polynomials over integers in independent symbols A, B, q.
    # q = deposit*(1-fee). Substitute y=q*B/(A+q) into
    # (A+q)*(B-y)-A*B, then clear the strictly positive denominator A+q.
    A, B, q = ({(1, 0, 0): 1}, {(0, 1, 0): 1}, {(0, 0, 1): 1})
    denom = add(A, q)
    negative_qB = {k: -v for k, v in mul(q, B).items()}
    first = mul(denom, add(mul(B, denom), negative_qB))
    second = {k: -v for k, v in mul(mul(A, B), denom).items()}
    require(add(first, second) == {}, 'symbolic AMM identity')
    checked = 0
    for ra in [1, 100, 100000]:
        for rb in [1, 200, 200000]:
            for deposit in [0, 1, 50000]:
                for fee in [Fraction(0), Fraction(3, 1000), Fraction(1)]:
                    effective = deposit*(1-fee)
                    output = effective*rb/(ra+effective)
                    require((ra+effective)*(rb-output) == ra*rb, 'exact AMM invariant')
                    require(0 <= output < rb, 'AMM output range')
                    checked += 1
    record('1.3 AMM formula', 'supported under stated assumptions',
           'Exact symbolic cancellation and rational tests verify the effective-input constant-product formula for positive reserves and fees in [0,1]. This does not establish a statistical expectation under random reserves.',
           exact_numeric_cases=checked, symbolic_residual_polynomial={})
    # Three independent Uniform(0,1) latencies have a continuous density,
    # mean 1.5 and variance .25. Their standardized CDF at 1 is exactly 5/6.
    x = 1.
    discrepancy = abs(5/6-float(norm.cdf(x)))
    record('1.3 latency normality', 'contradicted',
           'Increasing the number of observed samples does not change the population distribution of a fixed sum of three intervals. A sum of three independent uniform intervals retains a nonzero normal-CDF discrepancy.',
           exact_population_cdf=5/6, comparison_normal_cdf=float(norm.cdf(x)),
           discrepancy=discrepancy)
    record('1.3 standardized volume mean', 'insufficiently specified',
           'If residual = zero-mean oracle noise + Uniform(0,b) slippage, its mean is b/2. Subtracting the AMM formula and dividing by a scale does not itself center it.',
           example_b=2, residual_mean_before_centering=1)
    rng = np.random.default_rng(SEED)
    n = 40000
    rows = []
    for k in [2, 8, 32, 128]:
        independent = rng.normal(size=(n, k))
        iid_norm2 = np.square(independent).sum(axis=1)
        common = rng.normal(size=n)
        correlated_norm2 = k*common**2
        for epsilon in [.5, 1.2]:
            bound = 2*math.exp(-k*epsilon**2/(2*(1+epsilon/3)))
            cutoff = k*epsilon**2
            count = int((iid_norm2 <= cutoff).sum())
            exact = float(chi2.cdf(cutoff, k))
            rows.append({'K': k, 'epsilon': epsilon, 'paper_bound': bound,
                         'exact_iid_acceptance_probability': exact,
                         'iid_simulated_probability': count/n,
                         'iid_95pct_interval': interval(count, n),
                         'perfectly_correlated_probability': float((correlated_norm2 <= cutoff).mean()),
                         'bound_violated_by_exact_iid_probability': exact > bound})
    require(any(r['bound_violated_by_exact_iid_probability'] for r in rows), 'bound counterexample')
    record('1.3 false-positive bound', 'contradicted',
           'The acceptance event uses mean(Z^2)<=epsilon^2, whereas the proof bounds mean(Z^2)<=1-epsilon. They are different events. The universal epsilon>0 claim fails even for independent standard Gaussian null features.',
           results=rows)
    k, epsilon = 32, .5
    threshold = k*epsilon**2
    probability = float(chi2.cdf(threshold, k))
    delta = 1-epsilon**2
    corrected_bound = math.exp(k/2*(delta+math.log1p(-delta)))
    require(probability <= corrected_bound, 'corrected chi-square lower tail')
    record('1.3 conditional replacement bound', 'supported under stated assumptions',
           'For independent N(0,1) null features and 0<epsilon<1, delta=1-epsilon^2 gives the Chernoff bound exp(K/2*(delta+log(1-delta))). This model must be justified separately.',
           exact_probability=probability, corrected_bound=corrected_bound,
           probability_any_of_100000_independent_candidates=float(-math.expm1(100000*math.log1p(-probability))),
           poisson_mean_100000_candidates_probability=float(-math.expm1(-100000*probability)))
    # exp(-||z||^2/2) has peak one but is not a normalized Gaussian density.
    record('1.3 kernel normalization', 'insufficiently specified',
           'The score is bounded by one; its integral on R^K is (2*pi)^(K/2), not one. A similarity score is not itself a pseudo-metric.',
           integral_K2=2*math.pi)
    return results


# Intended validation: Definitions 1.3.1–1.3.3.
# Test squared Mahalanobis distance, covariance invertibility, transport
# asymmetry, threshold calibration, and equivalence-relation properties.
# Use numeric synthetic embeddings; hashes and addresses need an explicitly
# justified encoding before they can be used in a covariance geometry.


def quadratic(x, y, covariance):
    delta = np.asarray(x)-np.asarray(y)
    return float(delta @ np.linalg.solve(covariance, delta))


def validate_metric_and_equivalence():
    """Return all original findings for metric and equivalence."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    identity = np.eye(1)
    a, b, c = [0.], [1.], [2.]
    ab, bc, ac = [quadratic(x, y, identity) for x, y in [(a,b), (b,c), (a,c)]]
    require(ac > ab+bc, 'squared distance triangle counterexample')
    require(np.sqrt(ac) <= np.sqrt(ab)+np.sqrt(bc), 'root distance triangle')
    record('1.3.2 pseudo-metric', 'contradicted',
           'Even with identity transport and positive-definite covariance, the written quadratic form violates the triangle inequality. Its square root is the usual Mahalanobis distance on a common numeric space.',
           distances={'a_b': ab, 'b_c': bc, 'a_c': ac})
    gamma = 1.1
    relation = lambda x, y: quadratic(x, y, identity) <= gamma
    require(relation(a,b) and relation(b,c) and not relation(a,c), 'nontransitivity')
    record('1.3.3 equivalence', 'contradicted',
           'Threshold proximity is reflexive and symmetric in this restricted setup, but is not transitive. Transitive closure creates a new relation and can merge distant endpoints.',
           threshold=gamma, a_related_b=True, b_related_c=True, a_related_c=False)
    # Gamma(y)=y-1 in a one-dimensional shared-coordinate illustration.
    forward = (0-(2-1))**2
    reverse_with_same_transport = (2-(0-1))**2
    require(forward != reverse_with_same_transport, 'directional transport')
    record('1.3.2 cross-space domain', 'insufficiently specified',
           'The given domain Omega_A x Omega_B does not define a self-distance or a reverse distance. A shared embedding or compatible inverse transport is needed.',
           forward_cost=forward, reverse_cost_using_same_transport=reverse_with_same_transport)
    singular = np.array([[1., 1.], [1., 1.]])
    require(np.linalg.matrix_rank(singular) == 1, 'singular covariance')
    record('1.3.2 covariance and encoding', 'insufficiently specified',
           'Correlated or constant features can make covariance singular. Hash and asset-ID encoding, feature rank, covariance estimation, and bridge inverse domains must be specified.',
           example_covariance_rank=1, feature_count=2)
    alpha = 1e-6
    threshold = float(chi2.ppf(1-alpha, 6))
    acceptance = float(chi2.cdf(threshold, 6))
    require(abs(acceptance-(1-alpha)) < 1e-12, 'chi-square quantile')
    record('1.3.3 significance interpretation', 'contradicted',
           'If unrelated-pair squared distance is chi-square(6), as in the theorem null model, accepting below the 1-alpha quantile accepts 1-alpha of unrelated pairs. If chi-square instead models true pairs, a background model is still required for false positives.',
           alpha=alpha, threshold=threshold, null_acceptance_probability=acceptance)
    return results


# Intended validation: Proposition 1.4 and its reliability products.
# Reproduce the 0.999992 example exactly. Enumerate independent edge events
# and simulate independent versus shared-error paths. Test what edge
# disjointness does and does not imply about probabilistic independence.
# No calculation here establishes a legal standard or real-world ownership.


def validate_attribution_confidence():
    """Return all original findings for attribution confidence."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    confidence = 1-(1-Fraction(98, 100))**3
    require(confidence == Fraction(124999, 125000), 'published arithmetic')
    record('1.4 numeric example', 'supported under stated assumptions',
           'Three independent paths, each with success probability .98, give 0.999992.',
           exact_fraction=str(confidence), decimal=float(confidence))
    # Enumerate all 16 outcomes for two independent two-edge paths.
    probabilities = [Fraction(9, 10), Fraction(8, 10), Fraction(7, 10), Fraction(6, 10)]
    exact = Fraction(0)
    for outcomes in product([False, True], repeat=4):
        mass = Fraction(1)
        for p, succeeds in zip(probabilities, outcomes):
            mass *= p if succeeds else 1-p
        if (outcomes[0] and outcomes[1]) or (outcomes[2] and outcomes[3]):
            exact += mass
    formula = 1-(1-probabilities[0]*probabilities[1])*(1-probabilities[2]*probabilities[3])
    require(exact == formula, 'independent path enumeration')
    record('1.4 reliability products', 'supported under stated assumptions',
           'Exact enumeration confirms the product formula when all modeled edges are independent.',
           enumerated_fraction=str(exact), formula_fraction=str(formula))
    rng = np.random.default_rng(SEED)
    n = 100000
    independent = rng.random((n, 3)) < .98
    shared = rng.random(n) < .98
    correlated = np.repeat(shared[:, None], 3, axis=1)
    record('1.4 edge-disjoint independence', 'contradicted',
           'Three disjoint graph paths can depend on the same uncertain attribution premise. Perfectly correlated paths with marginal .98 have union probability .98, not .999992.',
           independent_theory=float(confidence), independent_simulation=float(independent.any(axis=1).mean()),
           shared_error_theory=.98, shared_error_simulation=float(correlated.any(axis=1).mean()),
           dependence_free_union_bounds=[.98, 1.])
    p = Fraction(98, 100)
    record('1.4 within-path dependence', 'contradicted',
           'Two edges both controlled by one Bernoulli(.98) premise have joint success .98. Multiplying their marginal probabilities gives .9604.',
           true_joint=float(p), product_of_marginals=float(p*p))
    # A union of valid path events is not automatically a posterior identity
    # probability. Posterior calculations need base rates and likelihoods.
    prior, sensitivity, false_positive = .001, .98, .02
    posterior = sensitivity*prior/(sensitivity*prior+false_positive*(1-prior))
    record('1.4 identity interpretation', 'insufficiently specified',
           'Path reliability is not automatically P(identity | evidence). A synthetic Bayes example illustrates the need for priors, calibrated evidence likelihoods, and ownership premises.',
           illustrative_prior=prior, illustrative_sensitivity=sensitivity,
           illustrative_false_positive=false_positive, illustrative_posterior=posterior)
    return results


# Intended validation: Definitions 1.4.1–1.4.3 and the identity mapping.
# Check matrix dimensions and transfer direction using source-row adjacency.
# Test multiple custodial identities, many-addresses-to-one-person mappings,
# third-party deposits, and the claimed equivalence between a nonzero entity
# projection and exceeding an attribution-confidence threshold.


def validate_entity_projection():
    """Return all original findings for entity projection."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    # Nodes 0,1: actor addresses. Nodes 2,3: VASP deposit addresses.
    adjacency = np.zeros((4, 4))
    adjacency[0, 2], adjacency[1, 3] = 10, 20
    actor = np.eye(4)[:, :2]
    vasp = np.eye(4)[:, 2:]
    paper = vasp.T @ adjacency @ actor
    corrected_matrix = vasp.T @ adjacency.T @ actor
    corrected_vector = corrected_matrix @ np.ones(2)
    require(paper.shape == (2, 2), 'paper expression dimension')
    require(np.all(paper == 0) and corrected_vector.tolist() == [10., 20.], 'exposure direction')
    record('1.4.1 exposure dimension and direction', 'contradicted',
           'P_VASP.T @ A @ P_actor has shape (number of VASP addresses, number of actor addresses), not a vector. For source-row adjacency, actor-to-VASP exposure uses A.T and a final sum over actor columns.',
           paper_shape=list(paper.shape), paper_matrix=paper.tolist(),
           corrected_exposure_vector=corrected_vector.tolist())
    # Represent documented identities using explicit one-hot numeric vectors.
    two_identities = np.eye(2)
    projected = two_identities @ np.sign(corrected_vector)
    one_identity = np.array([[1., 1.]]) @ np.sign(corrected_vector)
    require(projected.tolist() == [1., 1.] and one_identity.tolist() == [2.], 'identity projections')
    record('1.4.2 identity encoding', 'insufficiently specified',
           'One-hot identities make a numeric linear operator possible. The result can contain multiple identities, or a count of two for one identity; it is not automatically one legal identity.',
           two_identity_projection=projected.tolist(), same_identity_projection=one_identity.tolist())
    kyc = {'deposit_1': 'person_A', 'deposit_2': 'person_A'}
    injective = len(set(kyc.values())) == len(kyc)
    require(not injective, 'noninjective mapping')
    record('1.4 mapping injectivity', 'contradicted',
           'A well-defined unique customer per deposit address does not imply an injective or bijective map: two deposit addresses may map to the same customer.',
           synthetic_mapping=kyc, injective=injective)
    confidence, threshold = .2, .999999
    nonzero = bool(np.any(projected != 0))
    require(nonzero and confidence < threshold, 'projection threshold counterexample')
    record('1.4.3 confidence equivalence', 'contradicted',
           'Theta @ sign(exposure) contains no confidence variable or threshold. Positive exposure can produce a nonzero projection even with low confidence.',
           nonzero_projection=nonzero, confidence=confidence, threshold=threshold)
    # Minimal ownership countermodel: Alice sends to Bob's exchange deposit.
    owner = {'source': 'Alice', 'deposit_customer': 'Bob'}
    require(owner['source'] != owner['deposit_customer'], 'third-party payment')
    record('1.4 ownership inference', 'insufficiently specified',
           'A transfer to a deposit associated with Bob is compatible with a payment from Alice. A flow edge alone does not imply identical ownership.',
           synthetic_countermodel=owner)
    return results


VALIDATORS = (
    ('01_graph_and_tensor', validate_graph_and_tensor),
    ('02_peeling_entropy', validate_peeling_entropy),
    ('03_bridge_correlation', validate_bridge_correlation),
    ('04_metric_and_equivalence', validate_metric_and_equivalence),
    ('05_attribution_confidence', validate_attribution_confidence),
    ('06_entity_projection', validate_entity_projection),
)


def run_all():
    """Run all suites in order, using a fresh result list and original seeds."""
    sections = [dict(section=name, results=validate())
                for name, validate in VALIDATORS]
    counts = Counter(item['status'] for section in sections
                     for item in section['results'])
    return dict(
        title="Phase 1 Graph Entropy and Cross Chain Attribution Validation",
        script=Path(__file__).name,
        seed=SEED,
        environment=dict(python=platform.python_version(),
                         numpy=np.__version__, scipy=scipy.__version__),
        scope="Synthetic mathematical validation; no real identities or legal findings.",
        summary=dict(sections=len(sections), findings=sum(counts.values()),
                     status_counts=dict(counts)),
        sections=sections,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__ or
        "Run all six Phase 1 validation suites and report their findings as JSON.")
    parser.add_argument('--output', type=Path, help='Also save the JSON report to this path.')
    args = parser.parse_args()
    report = json.dumps(run_all(), indent=2, allow_nan=False)
    if args.output is not None:
        args.output.write_text(report + '\n', encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
