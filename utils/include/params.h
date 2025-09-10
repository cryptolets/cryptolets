#ifndef _PARAMS_H_
#define _PARAMS_H_

// -------------------------------------------------------------------
// Precision mode
// -------------------------------------------------------------------
#define PREC_SINGLE 0
#define PREC_MULTI  1

#ifndef PRECISION_MODE
  #define PRECISION_MODE PREC_SINGLE
#endif

#ifndef BITWIDTH
  #define BITWIDTH 64   // default bitwidth
#endif

#if PRECISION_MODE == PREC_MULTI
  #ifndef LIMBS
    #define LIMBS 4       // number of limbs
  #endif
  #define WBW (BITWIDTH / LIMBS) // word bitwidth
#endif

// -------------------------------------------------------------------
// Base Multiplier Config
// -------------------------------------------------------------------
#define MUL_NORMAL     0
#define MUL_KARATSUBA  1
#define MUL_SCHOOLBOOK 2

#ifndef MUL_TYPE
  #define MUL_TYPE MUL_NORMAL
#endif

// bitwidth for schoolbook or karatsuba, where it will stop decomposing and use normal mul
// For FPGA, this largely defined by how well the specific DSP handles a certian bitwidth (27-bit)
// For ASIC, this is defined by what max bitwidth there is a highly optimized mul lib (128-bit)
#ifndef BASE_MUL_WIDTH
  #define BASE_MUL_WIDTH 32
#endif

// how many times to use karatsuba decomp, before using schoolbook (from topdown)
#ifndef KAR_BASE_MUL_WIDTH
  #define KAR_BASE_MUL_WIDTH 32
#endif

// Inline whole mul funcs by default
#ifndef CCORE_MULS
  #define CCORE_MULS 0
#endif

// --- MOD SPECIFIC PARAMS ---
// Define if we want fixed q prime with const muls or not
#define FIXED_Q 0
#define VAR_Q   1

#ifndef Q_TYPE
#define Q_TYPE VAR_Q
#endif

// -------------------------------------------------------------------
// Point Addition Config
// -------------------------------------------------------------------
#define PADD_NORMAL     0
#define PADD_CYCLONEMSM 1  // https://eprint.iacr.org/2022/1396.pdf
#define PADD_HARDCAMLMSM 2 // https://dl.acm.org/doi/10.1145/3626202.3637577
#define PADD_BN128 3

#ifndef PADD_TYPE
  #define PADD_TYPE PADD_NORMAL
#endif

// Random (and Custom) Fixed q and q_prime's
#if Q_TYPE == FIXED_Q

#if BITWIDTH == 8
#define Q_HEX "0x29"
#define Q_PRIME_HEX "0xe7"
#elif BITWIDTH == 16
#define Q_HEX "28bb"
#define Q_PRIME_HEX "238d"
#elif BITWIDTH == 24
#define Q_HEX "0x2ca215"
#define Q_PRIME_HEX "0xc2e2c3"
#elif BITWIDTH == 32
#define Q_HEX "3f5bc17d"
#define Q_PRIME_HEX "5db8802b"
#elif BITWIDTH == 48
#define Q_HEX "37159212a7bf"
#define Q_PRIME_HEX "fb00a77ab7c1"
#elif BITWIDTH == 64
#define Q_HEX "2bef75dc43b36979"
#define Q_PRIME_HEX "519267a7c284f37"
#elif BITWIDTH == 96
#define Q_HEX "3be86bc9e4c1487aff40f9f7"
#define Q_PRIME_HEX "ac84114bbb524343c3e46839"
#elif BITWIDTH == 128
#define Q_HEX "2bb4aade35d3bec1f0db5c2c082a328d"
#define Q_PRIME_HEX "dd72fd376a70dd81e684fa0224c61fbb"
#elif BITWIDTH == 192
#define Q_HEX "298562e036ff487ac0abae5d9c2652113943cfe80bb64263"
#define Q_PRIME_HEX "a67df313b7dc82eda7fc9686c6d2b083d4736686435b0b5"
#elif BITWIDTH == 256 && PADD_TYPE == PADD_BN128
// BN128 curve - https://hackmd.io/@vivi432/bn128-in-c
#define Q_HEX "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47"
#define Q_PRIME_HEX "f57a22b791888c6bd8afcbd01833da809ede7d651eca6ac987d20782e4866389"
#elif BITWIDTH == 256
#define Q_HEX "37050a111aacec9bc1a7baf7ed0d1124425c3752b98195eb97940876f6ccf679"
#define Q_PRIME_HEX "747ad45060b8f6a871aaf39776d1d1844999e4fdcdd3d94a168e0dfc2dc6c37"
#elif NUM_BITS == 384 && PADD_TYPE == PADD_CYCLONEMSM
// BLS12-377 curve - https://neuromancer.sk/std/bls/BLS12-377#
#define Q_HEX "1ae3a4617c510eac63b05c06ca1493b1a22d9f300f5138f1ef3622fba094800170b5d44300000008508c00000000001"
#define Q_PRIME_HEX "bfa5205feec82e3d22f80141806a3cec5b245b86cced7a1335ed1347970debffd1e94577a00000008508bfffffffffff"
#elif BITWIDTH == 384
#define Q_HEX "23d64847e03fedd97463de6c0dcfa2dc411a30480c88736c10d8dcdc203df2098ca34dc9a387132731ef60360c327f0b"
#define Q_PRIME_HEX "c5c2979d7931584be209d261bd255edbdf34dd1becd994c9e10fabcc5830ab3f83493804fa809460b7db424849932b5d"
#elif BITWIDTH == 512
#define Q_HEX "25676c3095158a3260c68cbffc317bdc52a40d923c5d68f56148ab74049a54b6c2fd5272cca60995c9204f434408e35377696d6b23677109c9f823881ef2ccff"
#define Q_PRIME_HEX "ab4296aa741f58fe088a0fcc198c63d1a1fa8c3938bac6b1fa049d1bd79617c0363385510afea656b16ca04bcf5ea4a568a3a7d92fe7159959782b282c1bcd01"
#elif BITWIDTH == 768
#define Q_HEX "228352866084695cebd728fc6a0edda0c80dba0b53e5eb42bb558ee21fc1fe007a8e6e0c96158586d1fd9461ee2ece8df46a38622792d241c4d4bbb01ee609698a605bf2fad6bdf7eba1695f965248ba810db95a2c5a29e9c5ee0ab46f510947"
#define Q_PRIME_HEX "af186324e87aa66b90eebac1cb87f0dd8520ab222ca446005484877f98a5481ac5391de6a3ccdf3b731822dfd228d6a9bcc321237101aaf35988ff0517c386cd01f95302a03dce546399a197c5dce284fd676e38165d5f8d4000ce38e2a22f89"
#elif BITWIDTH == 1024
#define Q_HEX "3c603780e8c7ea5d5442c270d573763766150676142eeda2940dc851ee19dd7d188c1118aa7f747265d38ea8ca19957ea83913f4275479abfc10a356283825932707867e9c0b77992d833620b4c50b6fe84ee3b0f6a6020103a00de459615951b5eb9adb544062b20f363661c20ea313f2e5236cf0b8787da45a7c6edf7a34a3"
#define Q_PRIME_HEX "1a20ec9768392e77c7218f9916f2876d08f085fcbbecb3a1183392e8d6be49d90a24b6f5f654aabb3c48fe3907a41cdc345cf419c8d3e1fd3393d86390b28907f8e72eb1e011fc6999dfdd530787e6b4b509d95bcc4f52ccad1bc514585dfa877d224fe47e8f30881e0d20b2cca70f3eb65ff733d464fb65c124d82c8dfe0f5"
#endif

#endif

#endif // _PARAMS_H_
