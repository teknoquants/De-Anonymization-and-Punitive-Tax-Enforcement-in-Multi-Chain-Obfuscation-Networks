# Intended validation: Run all six original Phase 3 validation sections.
# Preserve their mathematical fixtures, counterexamples, assumptions and findings.
# Detailed intended-validation comments precede each section below.
# A successful run means all implementation checks completed; it does not mean
# every manuscript claim is supported. Findings retain their original statuses.
# Title: Phase 3 flight risk freeze and recovery validation
# Requires Python 3.9+; install dependencies: python -m pip install numpy scipy
# Run: python phase3_flight_risk_freeze_and_recovery_validation.py
# Save JSON: python phase3_flight_risk_freeze_and_recovery_validation.py --output phase3_results.json
# Standalone: no companion Python scripts or data files are required.


# MIT License
# Copyright (c) September 2026 Roger Cooperman; A.E. Petrunina V.V.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
from collections import Counter
import json
import platform
from pathlib import Path
import numpy as np
import scipy
import math
from scipy.integrate import quad
from itertools import product
from copy import deepcopy
from scipy.optimize import linprog

def require(condition, label):
    """Implementation self-check, not an assertion that the paper is correct."""
    if not condition:
        raise AssertionError(label)

def trigger(r,w,liability,threshold):
    if liability<=0:raise ValueError('Logarithm requires positive liability')
    return int(float(np.dot(w,r))*math.log(liability)>=threshold)

def transfer(state,amount,signature=True):
    if amount<=0:raise ValueError('Fixture uses positive transfer amounts')
    new=deepcopy(state)
    allowed=(state['balance_u']>=amount and signature and
             not state['blocked_u'] and not state['blocked_v'])
    if allowed:
        new['balance_u']-=amount;new['balance_v']+=amount
    return new,allowed

def optimize(values,liability,accessible,discounts=None):
    values=np.asarray(values,dtype=float)
    accessible=np.asarray(accessible,dtype=float)
    discounts=np.ones_like(values) if discounts is None else np.asarray(discounts,dtype=float)
    if liability<0 or np.any(values<0) or np.any((accessible<0)|(accessible>1)) or np.any((discounts<0)|(discounts>1)):
        raise ValueError('Invalid model inputs')
    realized=values*discounts
    result=linprog(-realized,A_ub=[realized],b_ub=[liability],
                   bounds=[(0,float(a)) for a in accessible],method='highs')
    require(result.success,'LP convergence')
    return float(-result.fun),result.x.tolist()

# Intended validation: Proposition 3.1.
# Check the killed drift process, survival and expected recovery under
# deterministic nonnegative hazards; include finite threshold crossing,
# finite reaction delays, and the conditions needed for asymptotic loss.

def validate_flight_process():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    v0, mu, hazard, epsilon = 100., .02, .05, 1.
    cutoff = math.log(v0/epsilon)/mu
    rows=[]
    for t in [0.,10.,30.,90.,cutoff,cutoff+1]:
        # V(t)=V0 exp(-mu*t) 1{no jump by t}; first jump kills the process.
        jump_survival=math.exp(-hazard*t)
        flight_survival=jump_survival if t<cutoff else 0.
        recovery=v0*math.exp(-mu*t)*flight_survival
        rows.append(dict(time=t,jump_survival=jump_survival,
                         threshold_survival=flight_survival,expected_recovery=recovery))
    mean_flight=(1-math.exp(-hazard*cutoff))/hazard
    numeric_mean=quad(lambda t:math.exp(-hazard*t),0,cutoff)[0]
    require(math.isclose(mean_flight,numeric_mean,rel_tol=1e-12),'mean stopping time')
    record('3.1 killed drift solution','supported under stated assumptions',
           'For constant positive drift and hazard, V(t)=V0*exp(-mu*t)*1{T>t}, T exponential. With 0<epsilon<V0, flight time is min(T, log(V0/epsilon)/mu).',
           threshold_time=cutoff,expected_flight_time=mean_flight,examples=rows)
    require(rows[-1]['jump_survival']>0 and rows[-1]['threshold_survival']==0,'threshold correction')
    record('3.1 finite-threshold survival','contradicted',
           'The displayed Poisson-only survival misses continuous depletion past a positive epsilon. It is valid before the deterministic crossing or in the zero-threshold limit, not at all times for the defined stopping time.')
    # A nonconstant deterministic intensity: lambda(t)=.01+.002*t.
    t=10.
    integrated=quad(lambda s:.01+.002*s,0,t)[0]
    require(math.isclose(integrated,.01*t+.001*t*t),'cumulative hazard')
    record('3.1 nonhomogeneous hazard','supported under stated assumptions',
           'For a deterministic locally integrable intensity, first-jump survival is exp(-integrated hazard). A stochastic intensity would need an appropriate conditional model and averaging.',
           integrated_hazard=integrated,survival=math.exp(-integrated))
    delay,slow_mu,slow_hazard=90.,.0001,.0001
    survival=math.exp(-slow_hazard*delay)
    recovered=v0*math.exp(-(slow_mu+slow_hazard)*delay)
    require(survival>.99 and recovered>98,'finite-delay counterexample')
    record('3.1 inevitable near-zero delayed recovery','insufficiently specified',
           'A finite delay and positive rates alone do not imply near-zero recovery. The claim needs numerical hazard/drift calibration and an explicit meaning of near zero; intensity divergence after notice is an additional assumption.',
           delay=delay,survival=survival,expected_recovery=recovered,
           rate_units='inverse units of delay; illustrative inputs, not empirical rates')
    # Strictly positive but integrable drift and hazard over [0,infinity).
    limiting_expectation=v0*math.exp(-.1-.2)
    require(limiting_expectation>0,'integrable rates limit')
    record('3.1 asymptotic zero recovery','insufficiently specified',
           'Before a threshold crossing, expected value is V0*exp(-integral(mu+lambda)). It tends to zero only if that cumulative integral diverges. Rates mu=.1*exp(-t), lambda=.2*exp(-t) are positive but integrable; choose epsilon below the limiting no-jump balance.',
           limiting_expected_value=limiting_expectation)
    reaction_delay=1.
    success=math.exp(-hazard*reaction_delay)
    require(0<success<1,'nonzero race risk')
    record('3.1 guaranteed preemption','contradicted',
           'Any fixed positive reaction delay has a positive probability of a jump first. In the exponential model, observing survival now does not predict the next jump. Zero delay and known positive initial balance give a special idealized case, not a telemetry guarantee.',
           reaction_delay=reaction_delay,success_probability=success)
    return results


# Intended validation: Definition 3.1.
# Test the trigger's equality boundary, logarithm domain, monetary-unit
# invariance, and monotonicity. Identify missing weights, feature scales,
# reference amount, calibration, and the distinction from legal authorization.

def validate_risk_trigger():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    r=np.array([1.,0.,0.]);w=np.array([1.,0.,0.])
    threshold=math.log(100.)
    require(trigger(r,w,100.,threshold)==1,'inclusive boundary')
    require(trigger(r,w,99.,threshold)==0,'below boundary')
    record('3.1.2 trigger arithmetic','supported under stated assumptions',
           'With fixed numeric conventions, the indicator is one at equality and zero below the threshold.')
    for value in [0.,-1.]:
        try:trigger(r,w,value,1.)
        except ValueError:pass
        else:raise AssertionError('nonpositive logarithm input')
    record('3.1.2 domain','insufficiently specified',
           'The formula requires strictly positive L. If R+ includes zero, the domain must be restricted or zero handled explicitly. Infinite or non-finite features also require an input policy.')
    dollars=trigger(r,w,100.,5.)
    cents=trigger(r,w,10000.,5.)
    require(dollars==0 and cents==1,'currency-unit counterexample')
    record('3.1.2 dimensional consistency','contradicted',
           'The same economic amount represented as 100 dollars or 10000 cents changes the decision if weights and threshold are fixed. A dimensionless log(L/Lref) or an explicit unit-dependent calibration is needed.',
           dollars_decision=dollars,cents_decision=cents)
    require(math.isclose(math.log(100/10),math.log(10000/1000)),'reference-unit invariance')
    record('3.1.2 reference-amount correction','supported under stated assumptions',
           'Using a reference amount expressed in the same monetary units makes log(L/Lref) invariant to conversion. This is a proposed correction, not the source formula.')
    low=trigger(-r,w,.1,1.);high=trigger(-r,w,10.,1.)
    require(low==1 and high==0,'negative-score monotonicity')
    record('3.1.2 monotonicity and calibration','insufficiently specified',
           'The stated real-valued feature domain allows a negative weighted score, so increasing liability can turn the trigger off. Weights, signs, feature units, derivative measurement and predictive calibration are unspecified.',
           low_liability_decision=low,high_liability_decision=high)
    record('3.1.2 authorization inference','insufficiently specified',
           'Computing a binary indicator does not establish a legal evidentiary threshold or authority to act. Those are external premises and were not tested as law.')
    return results


# Intended validation: Lemma 3.2.
# Exhaustively verify the supplied Boolean guard and an abstract atomic
# transfer. Test rejection without state mutation and distinguish blocked
# ordinary transfers from absorption under all possible state transitions.
# This is a toy state model, not a deployed contract implementation.

def validate_freeze_state_logic():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    rows=[]
    for sufficient,signature,blocked_u,blocked_v in product([False,True],repeat=4):
        state=dict(balance_u=10 if sufficient else 0,balance_v=3,
                   blocked_u=blocked_u,blocked_v=blocked_v)
        after,allowed=transfer(state,5,signature)
        expected=sufficient and signature and not blocked_u and not blocked_v
        require(allowed==expected,'guard truth table')
        require(after['balance_u']+after['balance_v']==state['balance_u']+state['balance_v'],'balance conservation')
        if not allowed:require(after==state,'rejection leaves modeled state unchanged')
        rows.append(dict(sufficient=sufficient,signature=signature,
                         blocked_sender=blocked_u,blocked_receiver=blocked_v,allowed=allowed))
    record('3.2 guard','supported under stated assumptions',
           'All 16 Boolean cases match the stated conjunctive precondition. In this model rejected calls leave balances and flags unchanged.',truth_table=rows)
    frozen=dict(balance_u=10,balance_v=0,blocked_u=True,blocked_v=False)
    _,allowed=transfer(frozen,1)
    require(not allowed,'ordinary transfer blocked')
    # An administrative unfreeze is a permitted countermodel transition,
    # not an assertion about any particular live stablecoin contract.
    unfrozen=deepcopy(frozen);unfrozen['blocked_u']=False
    _,after_unfreeze=transfer(unfrozen,1)
    require(after_unfreeze,'unfreeze countermodel')
    record('3.2 permanently absorbing state','contradicted',
           'A blocked sender cannot use this transfer while its flag remains set, but permanence under every transition is not proved. A model permitting an authorized flag reset satisfies the guard and allows later transfers.',
           before_unfreeze_allowed=allowed,after_unfreeze_allowed=after_unfreeze)
    record('3.2 scope of zero out-degree','insufficiently specified',
           'The guard constrains successful transfers of the modeled token. It does not constrain unrelated assets, all transaction attempts, administrative balance changes, or every ledger edge. A balance mapping also does not establish legal ownership.')
    record('3.2 freeze versus receipt','insufficiently specified',
           'Setting a Boolean flag leaves the balance at the original address. The model contains no treasury transfer or liquidation operation, so blocked movement alone does not establish realized recovery.',
           original_balance=frozen['balance_u'],treasury_receipt_in_model=0)
    return results


# Intended validation: Definitions 3.2.1–3.2.2.
# Check source-row restriction, receiver blocking, asset-specific scope,
# idempotence and nonnegative capacity reduction. Compare the left-only
# tensor operation to the two-endpoint guard supplied in Lemma 3.2.

def validate_restricted_tensor():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    a=np.array([[0.,5.,7.],[3.,0.,11.],[2.,13.,0.]])
    restriction=np.diag([0.,1.,1.])
    left=restriction@a
    both=restriction@a@restriction
    require(np.all(left[0,:]==0),'sender row zero')
    require(left[1,0]==3 and both[1,0]==0,'receiver guard mismatch')
    record('3.2.2 left restriction','supported under stated assumptions',
           'With A[i,j] denoting source i to destination j, left multiplication zeros the frozen source row.',result=left.tolist())
    record('3.2.2 two-endpoint consistency','contradicted',
           'Lemma 3.2 blocks both frozen senders and frozen receivers. R*A leaves incoming transfers to a frozen receiver nonzero. R*A*R matches both endpoint restrictions for this capacity model.',
           left_only_incoming=float(left[1,0]),two_sided_incoming=float(both[1,0]))
    tensor=np.stack([a,2*a],axis=2)
    restricted=tensor.copy()
    restricted[:,:,0]=restriction@tensor[:,:,0]@restriction
    all_assets=np.einsum('ij,jka->ika',restriction,tensor)
    require(np.array_equal(restricted[:,:,1],tensor[:,:,1]),'unaffected asset')
    require(all_assets[0,1,1]==0 and restricted[0,1,1]>0,'asset scope')
    record('3.2.1 asset specificity','insufficiently specified',
           'A restriction for one asset must be applied to that asset slice. A single unrestricted tensor multiplication would also suppress other assets; the definition must specify its asset domain.',
           unaffected_asset_outgoing=float(restricted[0,1,1]),indiscriminate_mask_outgoing=float(all_assets[0,1,1]))
    require(np.array_equal(restriction@both@restriction,both),'idempotence')
    require(np.all(both>=0) and np.all(both<=a),'capacity monotonicity')
    record('3.2 restriction algebra','supported under stated assumptions',
           'The Boolean diagonal mask is idempotent, preserves nonnegativity and cannot increase individual proposed capacities.')
    record('3.2 capacity versus history','insufficiently specified',
           'The mask applies to prospective transfer capacity under a stated execution policy. It does not erase prior transactions, prove future flag persistence, or model all balance and authorization constraints.')
    return results


# Intended validation: Theorem 3.3.
# Solve the idealized divisible-asset linear program and compare it with
# reachability limits, liquidation discounts, duplicate jurisdiction entries,
# and an indivisible-asset counterexample. Debt is an input, not a consequence
# assumed valid from Phase 2. No real asset or jurisdiction is involved.

def validate_recovery_optimization():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    values=[40.,60.,100.];wealth=sum(values)
    rows=[]
    for liability in [0.,50.,200.,300.]:
        recovery,allocation=optimize(values,liability,[1,1,1])
        require(np.isclose(recovery,min(liability,wealth)),'ideal optimum')
        rows.append(dict(liability=liability,recovery=recovery,allocation=allocation))
    record('3.3 ideal optimization','supported under stated assumptions',
           'If every asset is reachable, divisible, realizable at its stated value, and no other constraint applies, the optimum is min(liability,wealth).',examples=rows)
    recovery,allocation=optimize(values,300,[1,0,1])
    require(np.isclose(recovery,140),'unreachable asset')
    record('3.3 guaranteed attainability','contradicted',
           'The upper bounds R<=debt and R<=wealth do not establish that all wealth is attainable. A model with one inaccessible asset has debt 300, wealth 200, but maximum recovery 140.',
           liability=300,wealth=wealth,recovery=recovery,allocation=allocation)
    discounted,_=optimize(values,300,[1,1,1],[1,.8,.5])
    require(np.isclose(discounted,138),'realization discount')
    record('3.3 valuation and recoverability','insufficiently specified',
           'Market valuation need not equal realized proceeds. With explicitly stipulated realization factors 1, .8, .5, full asset access yields 138 rather than 200.',
           market_value=wealth,realized_value=discounted)
    indivisible=max(sum(v*b for v,b in zip([60,60],bits))
                    for bits in product([0,1],repeat=2)
                    if sum(v*b for v,b in zip([60,60],bits))<=100)
    require(indivisible==60,'indivisibility')
    record('3.3 feasibility details','insufficiently specified',
           'The scalar bound presumes a feasible allocation mechanism. Two indivisible assets worth 60 each and debt 100 yield a binary-model optimum of 60, versus 100 in a divisible model. Sales with returned surplus would be a different model.',
           binary_optimum=indivisible,divisible_optimum=100)
    local,_=optimize(values,300,[1,0,0])
    coalition,_=optimize(values,300,[1,1,0])
    require(local<=coalition<wealth,'coordination access comparison')
    record('3.3 multilateral coordination','supported under stated assumptions',
           'Expanding an otherwise identical feasible set cannot lower the optimum, but it need not reach total wealth.',
           local_recovery=local,coalition_recovery=coalition,wealth=wealth)
    record('3.3 asset and debt inputs','insufficiently specified',
           'Jurisdiction lists require unique asset IDs to avoid double counting. Ownership, encumbrances, net versus gross wealth, legal access, execution costs and timing require external inputs. Phase 2 did not establish a universal debt>wealth guarantee.',
           duplicated_asset_entries=[['jurisdiction_A','asset_1',100],['jurisdiction_B','asset_1',100]],
           naive_sum=200,unique_asset_value=100)
    return results


# Intended validation: Definitions 3.3.1–3.3.3.
# Check the recovery trace against quantity-times-price valuation, diagonal
# projection properties, missing convergence assumptions and debt caps.
# Distinguish an administrative freeze marker from actual treasury receipt.

def validate_treasury_projection():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    quantities=np.array([2.,3.]);prices=np.array([10.,20.])
    projection=np.eye(2)
    wealth=float(quantities@prices)
    paper=float(np.trace(projection@np.diag(prices)))
    corrected=float(np.trace(projection@np.diag(quantities*prices)))
    require(wealth==80 and paper==30 and corrected==wealth,'quantity omission')
    record('3.3.3 trace valuation','contradicted',
           'With W=w.T*v and v interpreted as unit prices, the proposed trace omits quantities. w=(2,3), v=(10,20) gives W=80, but Tr(I*diag(v))=30. Use quantities in the diagonal, or explicitly define each v entry as total asset value and w as inclusion indicators.',
           wealth=wealth,paper_trace=paper,quantity_adjusted_trace=corrected)
    p=np.diag([1.,0.])
    require(np.array_equal(p@p,p),'diagonal Boolean projection')
    binary=np.array([[1.,1.],[0.,1.]])
    require(not np.array_equal(binary@binary,binary),'binary not projection')
    record('3.3.2 projection structure','insufficiently specified',
           'A diagonal Boolean matrix is idempotent. Membership in {0,1}^{M x M} alone does not make a matrix a projection; off-diagonal entries must be constrained.',
           binary_nonprojection=binary.tolist(),square=(binary@binary).tolist())
    liability=100.
    partial=float(np.trace(p@np.diag(quantities*prices)))
    require(liability>wealth and partial<wealth,'debt does not force reachability')
    record('3.3.3 identity convergence','contradicted',
           'The constant path P(t)=diag(1,0) satisfies Boolean diagonal constraints and never reaches I despite debt>wealth. If every diagonal is stipulated to become one, convergence is assumed rather than derived from debt.',
           liability=liability,wealth=wealth,partial_recovery=partial)
    capped_debt=25.
    require(corrected>capped_debt,'uncapped projection')
    record('3.3.3 liability cap','insufficiently specified',
           'Outside the theorem\'s debt>wealth regime, the trace formula has no debt-cap input. A constrained allocation is needed to enforce the preceding R<=debt rule; simply freezing all assets does not implement it.',
           trace=corrected,alternative_debt=capped_debt)
    frozen_value=80.;received_value=0.
    record('3.3.3 freeze versus treasury receipt','insufficiently specified',
           'If a projection entry means frozen or subject to a lien, its value is not necessarily cash received. Recovery status must distinguish restriction, transfer, liquidation and receipt.',
           frozen_value=frozen_value,possible_treasury_receipt=received_value)
    return results


VALIDATORS = (
    ('01_flight_process', validate_flight_process),
    ('02_risk_trigger', validate_risk_trigger),
    ('03_freeze_state_logic', validate_freeze_state_logic),
    ('04_restricted_tensor', validate_restricted_tensor),
    ('05_recovery_optimization', validate_recovery_optimization),
    ('06_treasury_projection', validate_treasury_projection),
)

def run_all():
    """Run every section and return one structured report; safe to call again."""
    sections = [dict(section=name, results=validate()) for name, validate in VALIDATORS]
    counts = Counter(item['status'] for section in sections for item in section['results'])
    return dict(title='Phase 3 flight risk freeze and recovery validation', script=Path(__file__).name,
                environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
                scope="Mathematical fixtures only; no real identity or legal findings.",
                summary=dict(sections=len(sections), findings=sum(counts.values()),
                             status_counts=dict(counts)), sections=sections)


def main():
    parser = argparse.ArgumentParser(description='Phase 3 flight risk freeze and recovery validation')
    parser.add_argument('--output', type=Path, help='Also save the JSON report to this path.')
    args = parser.parse_args()
    report = json.dumps(run_all(), indent=2, allow_nan=False)
    if args.output is not None:
        args.output.write_text(report + '\n', encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
