# Intended validation: Run all six original Phase 5 validation sections.
# Preserve their mathematical fixtures, counterexamples, assumptions and findings.
# Detailed intended-validation comments precede each section below.
# A successful run means all implementation checks completed; it does not mean
# every manuscript claim is supported. Findings retain their original statuses.
# Title: Phase 5 ecdsa bip32 and merkle trie validation
# Requires Python 3.9+; install dependencies: python -m pip install cryptography
# Run: python phase5_ecdsa_bip32_and_merkle_trie_validation.py
# Save JSON: python phase5_ecdsa_bip32_and_merkle_trie_validation.py --output phase5_results.json
# Standalone: no companion Python scripts or data files are required.
# Public synthetic keys and nonces only; educational, not production cryptography.


# MIT License
# Copyright (c) September 2026 Roger Cooperman; A.E. Petrunina V.V.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
from collections import Counter
from cryptography.hazmat.primitives.asymmetric import ec,utils
from cryptography.hazmat.primitives import hashes
from copy import deepcopy
import json
import platform
import hashlib
import hmac
from pathlib import Path
import cryptography

def require(condition, label):
    """Implementation self-check, not an assertion that the paper is correct."""
    if not condition:
        raise AssertionError(label)

VECTORS=[
'xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi',
'xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7',
'xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs']

P=2**256-2**32-977

N=int('fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141',16)

G=(int('79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798',16),
   int('483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8',16))

def on_curve(q):
    return q is not None and 0<=q[0]<P and 0<=q[1]<P and (q[1]**2-q[0]**3-7)%P==0

def add(a,b):
    if a is None:return b
    if b is None:return a
    x,y=a;u,v=b
    if x==u and (y+v)%P==0:return None
    slope=((3*x*x)*pow(2*y,-1,P) if a==b else (v-y)*pow(u-x,-1,P))%P
    xx=(slope*slope-x-u)%P
    return xx,(slope*(x-xx)-y)%P

def mul(k,q=G):
    if k<0:return mul(-k,(q[0],(-q[1])%P))
    result=None
    while k:
        if k&1:result=add(result,q)
        q=add(q,q);k>>=1
    return result

def sign(z,d,k):
    if not 1<=d<N or not 1<=k<N:raise ValueError('invalid scalar')
    r=mul(k)[0]%N;s=pow(k,-1,N)*(z+r*d)%N
    if not r or not s:raise ValueError('invalid signature; choose another nonce')
    return r,s

def verify(z,sig,q):
    r,s=sig
    if not on_curve(q) or not 1<=r<N or not 1<=s<N:return False
    inv=pow(s,-1,N);point=add(mul(z*inv%N),mul(r*inv%N,q))
    return point is not None and point[0]%N==r

def ser(q):return bytes([2+(q[1]&1)])+q[0].to_bytes(32,'big')

def master(seed):
    i=hmac.new(b'Bitcoin seed',seed,hashlib.sha512).digest()
    k=int.from_bytes(i[:32],'big')
    if not 1<=k<N:raise ValueError('invalid master key')
    return k,i[32:]

def child(parent,index,public=False,forced_left=None):
    key,chain=parent
    if not 0<=index<2**32:raise ValueError('index out of range')
    if public and index>=2**31:raise ValueError('hardened public derivation unavailable')
    data=(b'\0'+key.to_bytes(32,'big') if index>=2**31 else ser(key if public else mul(key)))
    i=hmac.new(chain,data+index.to_bytes(4,'big'),hashlib.sha512).digest()
    left=int.from_bytes(i[:32],'big') if forced_left is None else forced_left
    if left>=N or left<0:raise ValueError('invalid child; caller must advance index')
    out=add(mul(left),key) if public else (left+key)%N
    if out is None or out==0:raise ValueError('invalid child; caller must advance index')
    return out,i[32:]

def decode58check(s):
    alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    number=0
    for c in s:number=58*number+alphabet.index(c)
    raw=b'\0'*(len(s)-len(s.lstrip('1')))+number.to_bytes((number.bit_length()+7)//8,'big')
    require(hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4]==raw[-4:],'base58 checksum')
    return raw[:-4]

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

def unpack(data):
    n=[v for b in data for v in (b>>4,b&15)]
    flag=n[0]
    if flag>3 or (not flag&1 and n[1]!=0):raise ValueError('invalid compact path')
    return (n[1:] if flag&1 else n[2:]),bool(flag&2)

def reference(node):return keccak(rlp(node)) if len(rlp(node))>=32 else node

def fixture(long_value=False):
    value=b'X'*40 if long_value else b'cat'
    leaf=[compact([],True),value];other=[compact([],True),b'dog']
    branch=[b'']*17;branch[3]=reference(leaf);branch[4]=reference(other)
    root=[compact([1,2],False),reference(branch)]
    return keccak(rlp(root)),[root,branch,leaf],value

def membership(root,path,value,proof):
    # Decoded-node fixture verifier: not a raw-wire RLP decoder or full client.
    expected=root;remaining=list(path)
    try:
        for node in proof:
            if isinstance(expected,bytes):
                if len(expected)!=32 or keccak(rlp(node))!=expected:return False
            elif node!=expected:return False
            if len(node)==17:
                if not remaining:return node[16]==value
                expected=node[remaining.pop(0)]
            elif len(node)==2:
                prefix,leaf=unpack(node[0])
                if remaining[:len(prefix)]!=prefix:return False
                remaining=remaining[len(prefix):]
                if leaf:return not remaining and node[1]==value
                expected=node[1]
            else:return False
    except (ValueError,TypeError,IndexError):return False
    return False

# Intended validation: Proposition 5.1 domain parameters and ECDSA equations.
# Check group identities, sign/verify substitution, independent OpenSSL-backed
# verification, and rejection of tampered messages, signatures and bad keys.

def validate_ecdsa_algebra():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    expanded=2**256-2**32-2**9-2**8-2**7-2**6-2**4-1
    require(expanded==P and on_curve(G) and mul(N) is None,'domain parameters')
    for d in [1,2,17,1234567,N-1]:
        independent=ec.derive_private_key(d,ec.SECP256K1()).public_key().public_numbers()
        require(mul(d)==(independent.x,independent.y),'independent group point')
    digest=hashlib.sha256(b'Phase 5 synthetic signature').digest();z=int.from_bytes(digest,'big')
    d,k=1234567,7654321;q=mul(d);r,s=sign(z,d,k)
    require(verify(z,(r,s),q),'valid signature')
    reconstructed=add(mul(z*pow(s,-1,N)%N),mul(r*pow(s,-1,N)%N,q))
    require(reconstructed==mul(k),'signature substitution')
    public=ec.EllipticCurvePublicNumbers(*q,ec.SECP256K1()).public_key()
    public.verify(utils.encode_dss_signature(r,s),digest,ec.ECDSA(utils.Prehashed(hashes.SHA256())))
    require(not verify(z+1,(r,s),q),'message mutation')
    require(not verify(z,(r,(s+1)%N),q),'signature mutation')
    for bad in [(0,s),(N,s),(r,0),(r,N)]:require(not verify(z,bad,q),'signature bounds')
    require(not verify(z,(r,s),(1,1)),'invalid public point')
    record('5.1 ECDSA algebra','supported under stated assumptions',
           'The field expression, generator order test, scalar multiplication and signature verification identity pass. Five public keys and a signature also match an independent cryptography/OpenSSL implementation.',
           independent_public_key_cases=5,tamper_and_range_checks=True)
    record('5.1 omitted preconditions','insufficiently specified',
           'A usable verifier also needs signature-range and public-point checks, rejection of infinity, hash-to-integer rules and valid nonzero signing outputs. The tests do not establish general computational hardness or legal attribution.')
    return results


# Intended validation: Proposition 5.1 validity and attribution implications.
# Use synthetic signatures to separate authorization from balance and nonce
# checks, test algebraic signature malleability, and exhibit identical-key
# holder models with different legal identities. No real private key is used.

def validate_signature_scope():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    z=int.from_bytes(hashlib.sha256(b'synthetic overspend').digest(),'big')
    d=19;q=mul(d);sig=sign(z,d,23)
    valid=verify(z,sig,q);balance,amount,expected_nonce,nonce=5,10,4,3
    accepted=valid and balance>=amount and nonce==expected_nonce
    require(valid and not accepted,'signature does not imply valid transaction')
    record('5.1 signature iff transition validity','contradicted',
           'A valid signature can authorize an overspend or wrong-nonce request that a ledger rejects. Signature verification alone is not sufficient for transaction validity.',
           signature_valid=valid,balance=balance,requested_amount=amount,transaction_accepted=accepted)
    r,s=sig
    require(verify(z,(r,N-s),q),'high-low s pair')
    record('5.1 mathematical versus protocol acceptance','supported under stated assumptions',
           'Both (r,s) and (r,n-s) satisfy ordinary ECDSA verification. Additional protocol rules may restrict accepted encodings or s values; the algebra alone does not specify them.')
    record('5.1 unique identity and intent','insufficiently specified',
           'A shared-key model with Alice and Bob holding the same synthetic key produces the same verification evidence as a sole-holder model. The signature equation has no legal-identity, authorization-history or intent input.')
    record('5.1 universal ledger scope','insufficiently specified',
           'The proposition quantifies over a ledger C without specifying its signature scheme or transition rules. The secp256k1 proof covers its stated ECDSA equations, not every consensus or contract authorization mechanism.')
    return results


# Intended validation: Lemma 5.2 derivation equations and serialization.
# Compare master, hardened child and normal grandchild with public BIP-32
# test-vector-1 private extended-key payloads, then cross-check CKDpub against
# the public key from CKDpriv over several normal indices.
# Reference: https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki

def validate_bip32_vectors():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    m=master(bytes.fromhex('000102030405060708090a0b0c0d0e0f'))
    hardened=child(m,2**31);normal=child(hardened,1)
    for key,vector in zip([m,hardened,normal],VECTORS):
        payload=decode58check(vector)
        require(len(payload)==78 and payload[:4]==bytes.fromhex('0488ade4'),'vector payload')
        require(payload[13:45]==key[1] and payload[45]==0 and int.from_bytes(payload[46:],'big')==key[0],'official key and chain code')
    for i in [0,1,2,1000,2**31-1]:
        priv=child(hardened,i);pub=child((mul(hardened[0]),hardened[1]),i,public=True)
        require(mul(priv[0])==pub[0] and priv[1]==pub[1],'normal CKD identity')
    record('5.2 BIP-32 derivation','supported under stated assumptions',
           'Master and two descendants match key and chain-code fields from BIP-32 vector 1. Private/public normal derivation agrees at five indices.',official_nodes=3,normal_indices=5)
    record('5.2 vector scope','insufficiently specified',
           'These selected vectors do not exhaust all BIP-32 serialization and malformed-input cases. The helper is a test implementation, not a wallet library.')
    return results


# Intended validation: Lemma 5.2 whole-tree and provenance claims.
# Test hardened public-derivation failure, the requirement for chain code,
# rare invalid-child branches with injected HMAC-left values, and the
# distinction between an extended-key relation and asset-flow provenance.

def validate_derivation_limits():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    m=master(bytes(range(16)));pub=(mul(m[0]),m[1])
    try:child(pub,2**31,public=True)
    except ValueError:pass
    else:raise AssertionError('hardened public derivation accepted')
    require(child(m,2**31)[0]>0,'hardened private derivation')
    record('5.2 entire derivation tree','contradicted',
           'A root extended public key cannot traverse a hardened edge. The tested hardened child is available from the extended private key but CKDpub rejects that index.')
    changed=(pub[0],bytes([pub[1][0]^1])+pub[1][1:])
    require(child(pub,7,True)[0]!=child(changed,7,True)[0],'chain code dependence')
    record('5.2 public-key inputs','supported under stated assumptions',
           'Normal derivation needs the extended public key: public point plus chain code and index. The same point with a changed chain code produces a different child.')
    tests=0
    for public,parent in [(False,m),(True,pub)]:
        for invalid in [N,N-m[0]]:
            try:child(parent,1,public,forced_left=invalid)
            except ValueError:tests+=1
            else:raise AssertionError('invalid child not rejected')
    require(tests==4,'invalid child branches')
    record('5.2 exceptional cases','insufficiently specified',
           'The paper omits invalid-left-scalar and zero/infinity child cases. Injected rare cases are rejected; BIP-32 callers must then advance the index. The helper raises rather than implementing a wallet retry policy.',forced_rejections=tests)
    record('5.2 provenance conclusion','insufficiently specified',
           'A derivation relation does not prove which addresses were used, which assets moved, or who legally owns them. Index ranges, hardened boundaries, address encodings, ledger observations and identity evidence remain separate inputs.')
    return results


# Intended validation: Theorem 5.3 trie construction and proof formula.
# Check Keccak known answers, RLP and compact paths; validate small decoded
# extension/branch/leaf membership proofs with inline and hashed children.
# Reject tampering and compare actual node hashing with the paper's simplified
# sibling-concatenation expression. This is not a production proof verifier.

def validate_mpt_membership():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    require(keccak(b'').hex()=='c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470','empty keccak')
    require(keccak(b'abc').hex()=='4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45','abc keccak')
    require(keccak(b'')!=hashlib.sha3_256(b'').digest(),'Keccak versus SHA3')
    require(rlp([b'cat',b'dog']).hex()=='c88363617483646f67','RLP vector')
    require(compact([1,2,3,4,5],False).hex()=='112345','compact vector')
    require(keccak(rlp(b'')).hex()=='56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421','empty trie root')
    roots=[]
    for long_value in [False,True]:
        root,proof,value=fixture(long_value)
        require(membership(root,[1,2,3],value,proof),'valid MPT fixture')
        require(not membership(root,[1,2,4],value,proof),'wrong path')
        require(not membership(root,[1,2,3],value+b'!',proof),'wrong value')
        corrupted=deepcopy(proof);corrupted[0][0]=compact([1,3],False)
        require(not membership(root,[1,2,3],value,corrupted),'tampered node')
        require(not membership(root,[1,2,3],value,proof[:-1]),'missing leaf')
        roots.append(root.hex())
    record('5.3 MPT membership fixtures','supported under stated assumptions',
           'Known-answer hashing/encoding checks and both inline-child and hashed-child fixtures pass. Membership rejects wrong paths, values, missing leaves and a mutated node.',fixture_roots=roots)
    root,proof,value=fixture(True)
    naive=keccak(value)
    for node in reversed(proof[:-1]):naive=keccak(naive+keccak(rlp(node)))
    require(naive!=root,'naive proof formula mismatch')
    require(isinstance(fixture(False)[1][1][3],list),'short child is inline')
    record('5.3 sibling-hash proof formula','contradicted',
           'MPT verification requires path-aware RLP nodes and may contain embedded short children. The paper\'s payload-plus-sibling-hash expression does not reconstruct this valid fixture root. It is not a specified Ethereum MPT verification algorithm.',
           valid_root=root.hex(),illustrative_naive_fold=naive.hex())
    record('5.3 verifier coverage','insufficiently specified',
           'These decoded-node membership fixtures do not cover raw-wire decoding, all malformed RLP, non-membership proofs, full state-trie construction or live headers. No full Ethereum-client conformance is claimed.')
    return results


# Intended validation: Theorem 5.3 cross-chain and attribution implications.
# Demonstrate that valid membership is separate from a trusted root, finalized
# source state, execution success, destination acceptance and replay controls.
# Test state-root commitment scope and timestamp non-uniqueness in synthetic
# models. No bridge or consensus protocol is implemented or contacted.

def validate_commitment_scope():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    root,proof,value=fixture(True)
    included=membership(root,[1,2,3],value,proof)
    trusted_root=False;execution_success=False;already_processed=True
    accepted=included and trusted_root and execution_success and not already_processed
    require(included and not accepted,'membership is not bridge authorization')
    record('5.3 membership iff minting','contradicted',
           'A proof can verify against a supplied root while a destination rejects it because the root is untrusted, the execution condition fails, or the event was processed. The required bridge policy is absent from the root-equality equation.',
           membership_valid=included,synthetic_bridge_acceptance=accepted)
    # RLP account [nonce,balance,storageRoot,codeHash], addressed by a
    # Keccak-derived key. This is a one-account state-trie fixture.
    address=bytes.fromhex('11'*20);key=keccak(address)
    nibbles=[v for b in key for v in (b>>4,b&15)]
    account=[0,100,keccak(rlp(b'')),keccak(b'')]
    state_root=keccak(rlp([compact(nibbles,True),rlp(account)]))
    mutated=account.copy();mutated[1]+=1
    changed=keccak(rlp([compact(nibbles,True),rlp(mutated)]))
    require(state_root!=changed,'balance mutation changes fixture root')
    record('5.3 state commitment','supported under stated assumptions',
           'Changing a committed balance changes the one-account fixture root. This demonstrates sensitivity in an example, not a proof that collisions are mathematically impossible.',
           original_root=state_root.hex(),changed_root=changed.hex())
    record('5.3 whole history and identity','insufficiently specified',
           'A current account-state commitment does not explicitly encode a legal identity or the entire transaction history. State, transaction and receipt commitments serve distinct purposes; correlating addresses remains a separate inference.')
    # Source reaches an accepted committed state while destination has not
    # received the message. Both states can be represented without contradiction.
    source_finalized=True;destination_delivered=False
    require(source_finalized and not destination_delivered,'asynchronous countermodel')
    record('5.3 strict cross-chain synchrony','contradicted',
           'A source commitment and valid proof do not require immediate destination delivery. A model with finalized source state and delayed destination processing satisfies the commitment equations but is asynchronous.')
    record('5.3 timestamp and finality guarantees','insufficiently specified',
           'The root equation contains neither a clock-accuracy bound nor a finality rule. Multiple ordered transactions can share one block timestamp. Sub-second timing and authenticated canonical roots require separate protocol evidence.',
           synthetic_transactions=[dict(index=0,timestamp=100),dict(index=1,timestamp=100)])
    return results


VALIDATORS = (
    ('01_ecdsa_algebra', validate_ecdsa_algebra),
    ('02_signature_scope', validate_signature_scope),
    ('03_bip32_vectors', validate_bip32_vectors),
    ('04_derivation_limits', validate_derivation_limits),
    ('05_mpt_membership', validate_mpt_membership),
    ('06_commitment_scope', validate_commitment_scope),
)

def run_all():
    """Run every section and return one structured report; safe to call again."""
    sections = [dict(section=name, results=validate()) for name, validate in VALIDATORS]
    counts = Counter(item['status'] for section in sections for item in section['results'])
    return dict(title='Phase 5 ecdsa bip32 and merkle trie validation', script=Path(__file__).name,
                environment=dict(python=platform.python_version(), cryptography=cryptography.__version__),
                scope="Mathematical fixtures only; no real identity or legal findings.",
                summary=dict(sections=len(sections), findings=sum(counts.values()),
                             status_counts=dict(counts)), sections=sections)


def main():
    parser = argparse.ArgumentParser(description='Phase 5 ecdsa bip32 and merkle trie validation')
    parser.add_argument('--output', type=Path, help='Also save the JSON report to this path.')
    args = parser.parse_args()
    report = json.dumps(run_all(), indent=2, allow_nan=False)
    if args.output is not None:
        args.output.write_text(report + '\n', encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
