# Intended validation: Run all six Phase 9 mathematical validations in one file.
# Check storage encoding and mutation, Shamir reconstruction and secrecy,
# builder revenue, and transaction-ordering/preemption claims.
# Successful execution means the checks ran; it does not mean every source
# claim is valid. Results distinguish support, contradiction and missing premises.
# Requires Python 3.11+ and only the standard library.
# Usage: python phase9_storage_shamir_and_preemption_validation.py
# Save results: python phase9_storage_shamir_and_preemption_validation.py --output phase9_results.json

# MIT License
# Copyright (c) September 2026 Roger Cooperman; A.E. Petrunina V.V.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json
import platform
from pathlib import Path

RESULTS=[]

def require(condition,label):
    if not condition:raise AssertionError(label)

def record(claim,status,explanation,**evidence):
    RESULTS.append(dict(claim=claim,status=status,explanation=explanation,evidence=evidence))

RC=[0x1,0x8082,0x800000000000808a,0x8000000080008000,0x808b,0x80000001,
    0x8000000080008081,0x8000000000008009,0x8a,0x88,0x80008009,0x8000000a,
    0x8000808b,0x800000000000008b,0x8000000000008089,0x8000000000008003,
    0x8000000000008002,0x8000000000000080,0x800a,0x800000008000000a,
    0x8000000080008081,0x8000000000008080,0x80000001,0x8000000080008008]
ROT=[[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
MASK=2**64-1

def rol(x,n):return ((x<<n)|(x>>(64-n)))&MASK if n else x

def keccak(data):
    rate=136
    pad=bytearray(data);pad.append(1)
    pad.extend(b'\0'*((-len(pad))%rate));pad[-1]|=128
    a=[0]*25
    for offset in range(0,len(pad),rate):
        for i in range(rate//8):a[i]^=int.from_bytes(pad[offset+8*i:offset+8*i+8],'little')
        for rc in RC:
            c=[a[x]^a[x+5]^a[x+10]^a[x+15]^a[x+20] for x in range(5)]
            d=[c[(x-1)%5]^rol(c[(x+1)%5],1) for x in range(5)]
            for x in range(5):
                for y in range(5):a[x+5*y]^=d[x]
            b=[0]*25
            for x in range(5):
                for y in range(5):b[y+5*((2*x+3*y)%5)]=rol(a[x+5*y],ROT[x][y])
            for x in range(5):
                for y in range(5):a[x+5*y]=b[x+5*y]^((~b[(x+1)%5+5*y])&b[(x+2)%5+5*y])
            a[0]^=rc
    return b''.join(x.to_bytes(8,'little') for x in a)[:32]

def rlp(value):
    if isinstance(value,int):value=b'' if value==0 else value.to_bytes((value.bit_length()+7)//8,'big')
    if isinstance(value,list):payload=b''.join(rlp(x) for x in value);short,long=192,247
    else:
        payload=value;short,long=128,183
        if len(payload)==1 and payload[0]<128:return payload
    size=len(payload)
    if size<56:return bytes([short+size])+payload
    size_bytes=size.to_bytes((size.bit_length()+7)//8,'big')
    return bytes([long+len(size_bytes)])+size_bytes+payload

def compact(path,leaf):
    flag=2*int(leaf)+len(path)%2
    nibbles=[flag]+path if len(path)%2 else [flag,0]+path
    return bytes(16*nibbles[i]+nibbles[i+1] for i in range(0,len(nibbles),2))



# Intended validation: Proposition 9.1 and Definition 9.1.1.
# Check fixed-width address/slot concatenation, Keccak known answers and a
# published mapping example; test zero, power-of-two and maximum slots against
# the logarithmic padding expression. No live storage locations are targeted.

def encode(address,slot):
    if not 0<=address<2**160 or not 0<=slot<2**256:raise ValueError('input out of range')
    return address.to_bytes(32,'big')+slot.to_bytes(32,'big')

def validate_storage_slot_encoding():
    require(keccak(b'').hex()=='c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470','Keccak empty vector')
    # Published Ethereum documentation storage-position example, not a target.
    address=int('391694e7e0b0cce554cb130d723a9d27458f9298',16)
    known=keccak(encode(address,1)).hex()
    require(known=='6661e9d6d8b923d5bbaab1b96e1dd51ff6ea2a93520fdc9eb75d059238b8c5e9','published slot vector')
    cases=0
    for a in [0,1,2**160-1]:
        for slot in [0,1,2,3,2**256-1]:
            preimage=encode(a,slot)
            require(len(preimage)==64 and int.from_bytes(preimage[:32],'big')==a and int.from_bytes(preimage[32:],'big')==slot,'fixed width')
            cases+=1
    record('9.1 mapping slot formula','supported under stated assumptions',
           'The 64-byte padded preimage and Keccak mapping calculation reproduce the published example and round-trip all 15 boundary fixtures.',known_slot=known,boundary_cases=cases)
    # For p=1, 256-log2(p)=256 zero bits plus bin(p) adds one more bit.
    total_bits=96+160+256+1
    require(total_bits==513,'log-padding off-by-one')
    record('9.1.1 logarithmic padding','contradicted',
           'As written, padding by 256-log2(p) is undefined at p=0, nonintegral for most p, and gives a 257-bit slot field for powers of two. At p=1 the full preimage has 513 rather than 512 bits. Fixed 32-byte encoding avoids these errors.',p1_preimage_bits=total_bits)
    record('9.1 layout prerequisites','insufficiently specified',
           'The base slot must come from the actual layout. Packing and inheritance prevent inferring it merely by counting declarations; proxy or custom layouts require their own resolution. Collision resistance is a security assumption, not an injectivity proof.')


# Intended validation: Proposition 9.1 and Definition 9.1.2.
# Apply an isolated Boolean write in synthetic storage, construct a one-slot
# trie-root example and test restoration; model call-frame rollback and gas
# accounting separately. This is not an EVM emulator or contract invocation.

def root_for(slot,value):
    if value==0:return keccak(rlp(b''))
    key=keccak(slot.to_bytes(32,'big'))
    path=[n for byte in key for n in (byte>>4,byte&15)]
    return keccak(rlp([compact(path,True),rlp(value)]))

def validate_storage_mutation():
    slot=12345;storage={slot:0,99:42};after=dict(storage);after[slot]=1
    require(after[99]==42 and after[slot]==1,'isolated write')
    before_root=root_for(slot,0);frozen_root=root_for(slot,1)
    require(before_root!=frozen_root,'fixture root mutation')
    restored=dict(after);restored[slot]=0
    require(root_for(slot,restored[slot])==before_root,'restored storage root')
    record('9.1.2 isolated state update','supported under stated assumptions',
           'The synthetic operator changes only its designated key; the one-slot trie example changes root when zero becomes one.',before_root=before_root.hex(),frozen_root=frozen_root.hex())
    record('9.1 irreversible mutation','contradicted',
           'A permitted administrative write from one back to zero restores this storage value and one-slot storage root. Irreversibility is not a consequence of hashing. This does not imply the global state root is restored: nonce, gas and other state may differ.')
    allowed=lambda state:state[slot]==0
    require(not allowed(after) and allowed(restored),'guard restoration')
    record('9.1 universal token guard','insufficiently specified',
           'Blocking follows only for transfer paths that actually consult this flag. Slot arithmetic alone does not establish guard coverage, administrative authority, immutability or behavior of every token implementation.')
    snapshot={'balance':10};working=dict(snapshot);working['balance']=0
    working=dict(snapshot)
    gas_limit,gas_consumed=100000,30000
    require(working==snapshot and gas_limit-gas_consumed==70000,'rollback gas distinction')
    record('9.1 REVERT and gas','insufficiently specified',
           'An ordinary REVERT rolls back the failing frame while preserving unused gas, subject to its own execution costs. If burning the caller\'s gas means all supplied gas, that interpretation is incorrect; consumed gas remains charged. The fixture illustrates the distinction, not exact opcode metering.',
           illustrative_gas_supplied=gas_limit,illustrative_gas_consumed=gas_consumed,illustrative_gas_remaining=gas_limit-gas_consumed)


# Intended validation: Lemma 9.2 and Definitions 9.2.1–9.2.3.
# Reconstruct synthetic secrets from every threshold subset using Lagrange
# weights; independently solve the transposed Vandermonde system. Test
# duplicate/zero coordinates and tampered shares without simulating signatures.

from itertools import combinations

PAPER_Q=2**256-432420386565659656852420874635263103247
# Explicit correction, not a silent substitution for the source parameter.
Q=int('fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141',16)

def evaluate(coefficients,x,q):
    y=0
    for a in reversed(coefficients):y=(y*x+a)%q
    return y

def weights(xs,q):
    if any(x%q==0 for x in xs) or len(set(x%q for x in xs))!=len(xs):raise ValueError('coordinates must be distinct and nonzero')
    result=[]
    for i,x in enumerate(xs):
        numerator=denominator=1
        for j,y in enumerate(xs):
            if j!=i:numerator=numerator*(-y)%q;denominator=denominator*(x-y)%q
        result.append(numerator*pow(denominator,-1,q)%q)
    return result

def solve(matrix,b,q):
    a=[[x%q for x in row]+[b[i]%q] for i,row in enumerate(matrix)];n=len(b)
    for j in range(n):
        pivot=next(i for i in range(j,n) if a[i][j])
        a[j],a[pivot]=a[pivot],a[j]
        inv=pow(a[j][j],-1,q);a[j]=[x*inv%q for x in a[j]]
        for i in range(n):
            if i!=j:
                factor=a[i][j];a[i]=[(u-factor*v)%q for u,v in zip(a[i],a[j])]
    return [row[-1] for row in a]

def validate_shamir_reconstruction():
    require(Q==2**256-432420386565659656852420866394968145599,'standard group order')
    witness=pow(2,PAPER_Q-1,PAPER_Q)
    require(PAPER_Q!=Q and witness!=1,'source parameter is wrong and composite')
    record('9.2 stated field modulus','contradicted',
           'The source decimal expression is not the secp256k1 group order. Its base-two Fermat residue is not one, which proves it composite. Modular arithmetic modulo this number is not a prime field. Subsequent reconstruction tests explicitly use the standard prime order.',
           source_modulus=str(PAPER_Q),standard_modulus=str(Q),
           source_minus_standard=str(PAPER_Q-Q),fermat_base_two_residue=str(witness),
           correct_subtracted_constant='432420386565659656852420866394968145599')
    coefficients=[123456789,17,29];shares={x:evaluate(coefficients,x,Q) for x in range(1,6)}
    checked=0
    for xs in combinations(shares,3):
        lam=weights(xs,Q)
        recovered=sum(l*shares[x] for l,x in zip(lam,xs))%Q
        vandermonde=[[pow(x,j,Q) for j in range(3)] for x in xs]
        transposed=list(map(list,zip(*vandermonde)))
        independent=solve(transposed,[1,0,0],Q)
        require(recovered==coefficients[0] and independent==lam,'independent interpolation')
        checked+=1
    record('9.2 reconstruction and synthesis vector','supported under stated assumptions',
           'Using the explicitly corrected prime field, all ten three-of-five subsets recover the synthetic secret. Solving V.T*lambda=e1 independently matches Lagrange weights, validating lambda=(V inverse).T*e1.',tested_subsets=checked)
    for xs in [[0,1,2],[1,1,2]]:
        try:weights(xs,Q)
        except ValueError:pass
        else:raise AssertionError('invalid coordinates accepted')
    xs=[1,2,3];lam=weights(xs,Q);ys=[shares[x] for x in xs];ys[0]+=1
    wrong=sum(a*b for a,b in zip(lam,ys))%Q
    require(wrong!=coefficients[0],'tampered share changes result')
    record('9.2 integrity and key domain','insufficiently specified',
           'Interpolation requires valid distinct coordinates and authentic shares. A modified share changes the result without inherent detection. A curve private scalar must also exclude zero, though the field itself includes zero. These tests do not implement verifiable sharing or signing.')


# Intended validation: Lemma 9.2 secrecy and unique-polynomial proof.
# Exhaustively enumerate a small prime field to count polynomials compatible
# with fewer-than-threshold shares, test uniform versus nonuniform priors,
# and distinguish sharing from a threshold-signature protocol.

from itertools import product
from fractions import Fraction as F

def compatible(q,observations,nonzero_leading=False):
    counts=[0]*q
    for secret,a,b in product(range(q),repeat=3):
        if nonzero_leading and b==0:continue
        if all((secret+a*x+b*x*x)%q==y for x,y in observations):counts[secret]+=1
    return counts

def validate_shamir_secrecy():
    q=5;one=[(1,2)];two=[(1,2),(2,3)]
    one_counts=compatible(q,one);two_counts=compatible(q,two)
    require(one_counts==[5]*5 and two_counts==[1]*5,'compatible counts')
    record('9.2 polynomial uniqueness','contradicted',
           'With t=3 and k=1 observed share, each candidate secret admits five degree-at-most-two polynomials over F5, not a unique polynomial. Uniqueness occurs at k=t-1. In general the count is q^(t-1-k).',
           one_share_counts=one_counts,two_share_counts=two_counts)
    posterior=[F(n,sum(one_counts)) for n in one_counts]
    require(posterior==[F(1,5)]*5,'uniform posterior')
    record('9.2 shares-only secrecy','supported under stated assumptions',
           'Uniform independent masking coefficients give equal likelihood for every secret in this exhaustive fixture. With a uniform secret prior, the posterior is uniform.',posterior=[str(x) for x in posterior])
    prior=[F(1,2)]+[F(1,8)]*4
    unnormalized=[p*F(n,25) for p,n in zip(prior,one_counts)]
    biased=[x/sum(unnormalized) for x in unnormalized]
    require(biased==prior,'prior preserved')
    record('9.2 unconditional 1/q posterior','insufficiently specified',
           'Sharing preserves the prior rather than forcing it to become uniform. The displayed 1/q needs a uniform field-secret prior and conditioning only on shares; restricting to nonzero private scalars or publishing other information changes that formulation.',nonuniform_posterior=[str(x) for x in biased])
    exact_degree=compatible(q,two,True)
    require(0 in exact_degree and max(exact_degree)==1,'forcing exact degree leaks in fixture')
    record('9.2 degree convention','insufficiently specified',
           'Coefficients sampled uniformly from the full field define degree at most t-1. Forcing a nonzero leading coefficient changes the distribution: the two-share fixture excludes one candidate secret. The implementation must preserve the specified randomness model.',exact_degree_counts=exact_degree)
    require(sum([7])%17==7,'threshold one example')
    record('9.2 custody and signing guarantees','insufficiently specified',
           'A t=1 scheme permits one holder to reconstruct, so a no-single-holder claim needs t>=2. Sharing alone does not implement DKG, authenticated signing, misuse prevention or availability. FROST is a Schnorr threshold protocol, not an ECDSA signing construction; no signing protocol is implemented here.')


# Intended validation: Theorem 9.3 builder-profit algebra.
# Test burned base fees, the fee-cap-adjusted priority payment, the restricted
# two-choice inequality and an exhaustive toy gas-capacity opportunity-cost
# counterexample. No bids, transactions or builder connections are submitted.

from itertools import combinations

def validate_builder_revenue():
    # Arbitrary consistent monetary/gas units, not live fee quotes.
    gas,base,max_fee,max_tip=100,10,12,5
    tip=min(max_tip,max_fee-base)
    builder=gas*tip;burn=gas*base
    require(tip==2 and builder==200 and burn==1000,'fee split')
    record('9.3 revenue objective','contradicted',
           'The base fee is burned rather than builder/proposer revenue under EIP-1559. Effective priority payment is also capped by max_fee-base_fee, so it need not equal maxPriorityFeePerGas.',
           priority_revenue=builder,burned_base_fee=burn,source_base_plus_tip_total=gas*(base+max_tip))
    u,bid,common=10,11,20
    require(bid+common>u+common,'restricted inequality')
    record('9.3 two-choice comparison','supported under stated assumptions',
           'B>U selects the bundle only in a two-choice model with equal residual revenues and costs, feasibility, and no better alternatives.',bundle_profit=bid+common,alternative_profit=u+common)
    # Items: label, gas, revenue. E and S are mutually exclusive.
    items=[('S',10,11),('E',1,10),('X',9,50)];capacity=10
    feasible=[]
    for size in range(4):
        for subset in combinations(items,size):
            names={x[0] for x in subset}
            if {'S','E'}<=names or sum(x[1] for x in subset)>capacity:continue
            feasible.append((sum(x[2] for x in subset),sorted(names)))
    optimum=max(feasible)
    require(bid>u and optimum==(60,['E','X']),'opportunity cost counterexample')
    record('9.3 bid sufficient for optimal inclusion','contradicted',
           'Even a rational local builder can reject B>U when the bundle displaces other revenue. With gas cap 10, S consumes 10 and pays 11; E consumes 1 and pays 10; compatible X consumes 9 and pays 50. E+X pays 60.',optimal_revenue=optimum[0],selected=optimum[1])
    record('9.3 profit notation and bid calibration','insufficiently specified',
           'The two residual fee sums must be defined consistently to avoid counting E twice. The initial asset-value-times-bribe-factor bound is not linked to opportunity costs or competing payloads. A local best response in a simplified model is not a dominant strategy across unspecified rivals.')


# Intended validation: Theorem 9.3 and Definitions 9.3.1–9.3.3.
# Enumerate feasible toy orderings with precedence constraints; distinguish
# requested first position, actual inclusion, execution success and effective
# state blocking. No live mempool access, routing or interception is performed.

from itertools import permutations

def validate_preemption_conditions():
    orders=list(permutations(['prepare','seize','other']))
    feasible=[p for p in orders if p.index('prepare')<p.index('seize')]
    require(feasible and all(p.index('seize')!=0 for p in feasible),'precedence versus first position')
    record('9.3 bid guarantees index zero','contradicted',
           'If a transaction needs a same-block prerequisite, no feasible ordering places it first, regardless of bid. Revenue optimization needs execution and precedence constraints, not only a permutation score.',feasible_orders=[list(p) for p in feasible])
    preferred_builder_selected=False;bundle_received=True;locally_profitable=True
    included=bundle_received and locally_profitable and preferred_builder_selected
    require(not included,'local choice not global inclusion')
    record('9.3 private delivery guarantees next block','insufficiently specified',
           'Local delivery and a favorable bid do not establish that the receiving builder supplies the selected next block. Selection, deadlines, eligibility and execution remain separate events. No probabilities for these events are specified.')
    sequence=['seize','evader'];indicator=int(sequence.index('seize')<sequence.index('evader'))
    freeze_executed=False;blocks_target=False
    achieved=bool(indicator and freeze_executed and blocks_target)
    require(indicator==1 and not achieved,'order not successful capture')
    record('9.3.3 order indicator interpretation','contradicted',
           'The indicator only describes relative positions of included transactions. It can be one while the first transaction fails or changes irrelevant state. If either transaction is omitted, the displayed ranking needs an explicit undefined/absent convention.',order_indicator=indicator,effective_preemption=achieved)
    one_based={'seize':1,'evader':2}
    zero_based={k:v-1 for k,v in one_based.items()}
    require(zero_based['seize']==0 and one_based['seize']==1,'index conversion')
    record('9.3.2 permutation types and indices','insufficiently specified',
           'A permutation of integers cannot be applied directly to transaction objects without an ID map. The document mixes first position 1 with transaction index 0; these conventions need a conversion. Inclusion/subset selection is not represented by permuting a fixed set.')
    record('9.3 conditional preemption','supported under stated assumptions',
           'If the intended transactions are included, the freeze succeeds first, and its state change invalidates the later operation, that later operation fails in the toy model. Those premises are stronger than B>U and contain no legal authorization conclusion.')


# Intended validation orchestration: run every check, count claim assessments,
# and emit one JSON report. Assertion failures indicate a failed validation
# fixture and produce a nonzero exit; contradicted source claims are findings.
def main():
    import argparse
    from collections import Counter

    parser = argparse.ArgumentParser(description="Self-contained Phase 9 validation.")
    parser.add_argument("--output", type=Path, help="Also save the JSON report to this path.")
    args = parser.parse_args()
    RESULTS.clear()
    validate_storage_slot_encoding()
    validate_storage_mutation()
    validate_shamir_reconstruction()
    validate_shamir_secrecy()
    validate_builder_revenue()
    validate_preemption_conditions()
    report = {
        "phase": 9,
        "python": platform.python_version(),
        "scope": "Synthetic offline mathematics and protocol checks; no real keys or enforcement.",
        "conclusion": "Phase 9 is not validated as a whole.",
        "assessment_counts": dict(Counter(item["status"] for item in RESULTS)),
        "results": RESULTS,
    }
    payload = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
