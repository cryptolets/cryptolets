# Tessera
Privacy-preserving computation encompasses powerful cryptographic techniques that allow parties to prove statements about (Zero-Knowledge Proofs, ZKPs) or compute on (Fully Homomorphic Encryption, FHE) sensitive data without disclosing it. Despite their potential applications, these techniques have seen limited deployment due to their high computational overhead. While a large body of research aims to accelerate these techniques, research groups largely operate in silos. Researchers new to working on privacy chips must build everything from scratch. To address this, we present _Tessera_, an open-source hardware framework for exploring and optimizing cryptographic kernels. Tessera provides a library of foundational large integer, modular, and elliptic curve (EC) arithmetic kernels, along with the Number Theoretic Transform (NTT), for ZKPs and FHE.


## Setup

```
pip install -e .
```

## Usage

```
tessera <command>
```
