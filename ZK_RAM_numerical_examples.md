# Zero-Knowledge RAM — Worked Numerical Examples

Concrete, hand-checkable examples for the construction in
*"Two Shuffles Make a RAM: Improved Constant Overhead Zero Knowledge RAM"*
(Yang & Heath, USENIX Security 2024), as implemented in this repository
(`zk-ram/ram.h`, `zk-ram/rom.h`, `zk-ram/inset_rom.h`).

> **Field note.** The real code works over the Mersenne prime
> `p = 2^61 − 1 = 2305843009213693951` (`emp-zk/emp-vole/utility.h`, `PR`).
> For legibility, all hand arithmetic below uses the toy prime **`p = 101`**.
> Nothing about the structure changes; only the numbers get smaller.

---

## 1. The example RAM

A memory of size **`N = 2`** (addresses `0` and `1`), subjected to **`T = 4`**
accesses.

| address | initial value | initial timestamp |
|:------:|:------:|:------:|
| `0` | `4` | `0` |
| `1` | `9` | `0` |

So `init_val = [4, 9]`. The access program we will run:

| # (clock `T`) | operation | `rw` | `addr` | `val` arg |
|:--:|:--|:--:|:--:|:--:|
| 1 | `read  mem[0]`      | 0 | 0 | – |
| 2 | `store mem[1] ← 7`  | 1 | 1 | 7 |
| 3 | `read  mem[1]`      | 0 | 1 | – |
| 4 | `store mem[0] ← 6`  | 1 | 0 | 6 |

Recall the multiplexer in `ram.h:71`:
`new_val = old_val + rw·(val − old_val)`, so `rw = 0` ⇒ value unchanged (a
read), `rw = 1` ⇒ value becomes `val` (a store). Every access — read or
store — still appends a fresh write tuple stamped with the new clock.

---

## 2. Setup phase (`IZKRAM::Setup`, ram.h:47)

For each address `i`, push `(idx=i, timestamp=0, val=init_val[i])` onto
`write_list`, and set `latest_pos[i] = i`. Only the *value* is a committed
prover input (`IntFp(init_val[i], ALICE)`); `idx` and `timestamp` are public.

`write_list` after Setup:

| pos | idx | ts | val | source |
|:--:|:--:|:--:|:--:|:--|
| 0 | 0 | 0 | 4 | setup |
| 1 | 1 | 0 | 9 | setup |

`latest_pos = [0, 1]`.

The bound-check set `bound_check_rom = InsetZKROM(total_T=4)` is also set up
here, holding the public key set `{1, 2, 3, 4}` (inset_rom.h:43).

---

## 3. Access phase (`IZKRAM::Access`, ram.h:60), step by step

For each access: read the latest tuple for `addr` (commit `old_timestamp`
and `old_val` as the **2 prover inputs**), append the read tuple, append a new
write tuple stamped `++T`, and feed `diff = newclock − old_ts` to the set.

### Access #1 — `read mem[0]` (`rw=0`)
- `pos = latest_pos[0] = 0` → `old_ts = 0`, `old_val = 4`
- **read tuple** `(0, 0, 4)`
- `new clock = 1`, `new_val = 4 + 0·(…) = 4` → **write tuple** `(0, 1, 4)` at pos `N+T−1 = 2`
- `latest_pos[0] = 2`
- `diff = 1 − 0 = 1` → set.Access(1)

### Access #2 — `store mem[1] ← 7` (`rw=1`)
- `pos = latest_pos[1] = 1` → `old_ts = 0`, `old_val = 9`
- **read tuple** `(1, 0, 9)`  ← captures the **old** value 9
- `new clock = 2`, `new_val = 9 + 1·(7−9) = 7` → **write tuple** `(1, 2, 7)` at pos `3`
- `latest_pos[1] = 3`
- `diff = 2 − 0 = 2` → set.Access(2)

> **On the "(1,0,9) looks wrong" question.** It is correct. On a *store*, the
> read tuple records the value that was there **before** (9), and the write
> tuple records the **new** value (7). The read must consume the previous
> write so the reads-multiset still matches the writes-multiset; the store's
> effect lives entirely in the new write tuple.

### Access #3 — `read mem[1]` (`rw=0`)
- `pos = latest_pos[1] = 3` → `old_ts = 2`, `old_val = 7`
- **read tuple** `(1, 2, 7)`
- `new clock = 3`, `new_val = 7` → **write tuple** `(1, 3, 7)` at pos `4`
- `latest_pos[1] = 4`
- `diff = 3 − 2 = 1` → set.Access(1)

### Access #4 — `store mem[0] ← 6` (`rw=1`)
- `pos = latest_pos[0] = 2` → `old_ts = 1`, `old_val = 4`
- **read tuple** `(0, 1, 4)`
- `new clock = 4`, `new_val = 4 + (6−4) = 6` → **write tuple** `(0, 4, 6)` at pos `5`
- `latest_pos[0] = 5`
- `diff = 4 − 1 = 3` → set.Access(3)

Final `latest_pos = [5, 4]`.

---

## 4. Teardown phase (`IZKRAM::Teardown_Basic`, ram.h:82)

Append one **final read** per address, reading whatever the last write left
behind (so every outstanding write gets consumed exactly once):

- address `0`: `latest_pos[0] = 5` → `write_list[5] = (0, 4, 6)` ⇒ read tuple `(0, 4, 6)`
- address `1`: `latest_pos[1] = 4` → `write_list[4] = (1, 3, 7)` ⇒ read tuple `(1, 3, 7)`

### Complete `write_list` (`N + T = 6` tuples)

| pos | idx | ts | val | source |
|:--:|:--:|:--:|:--:|:--|
| 0 | 0 | 0 | 4 | setup |
| 1 | 1 | 0 | 9 | setup |
| 2 | 0 | 1 | 4 | access 1 |
| 3 | 1 | 2 | 7 | access 2 |
| 4 | 1 | 3 | 7 | access 3 |
| 5 | 0 | 4 | 6 | access 4 |

### Complete `read_list` (`N + T = 6` tuples)

| order | idx | ts | val | source |
|:--:|:--:|:--:|:--:|:--|
| 1 | 0 | 0 | 4 | access 1 |
| 2 | 1 | 0 | 9 | access 2 |
| 3 | 1 | 2 | 7 | access 3 |
| 4 | 0 | 1 | 4 | access 4 |
| 5 | 0 | 4 | 6 | teardown (addr 0) |
| 6 | 1 | 3 | 7 | teardown (addr 1) |

---

## 5. First shuffle — reads ≡ writes as multisets

The core RAM invariant: **`read_list` and `write_list` are permutations of
each other.** Sort both as sets of `(idx, ts, val)` triples:

```
writes : {(0,0,4), (1,0,9), (0,1,4), (1,2,7), (1,3,7), (0,4,6)}
reads  : {(0,0,4), (1,0,9), (1,2,7), (0,1,4), (0,4,6), (1,3,7)}
```

Same six triples. ✓ The lists differ only in **order** — exactly what a
permutation proof checks.

> Why this implies correct RAM behavior: every write is read exactly once, and
> the monotone public clock (each write's `ts` strictly increases) forces each
> read to consume the *most recent* prior write to its address. A wrong value
> would break the multiset equality (see §7).

---

## 6. The polynomial / product check (`ram.h:121–129`)

The verifier samples random `A0, A1, A2, X`. Each tuple is compressed to one
field element

```
c(idx, ts, val) = A0·idx + A1·ts + A2·val + X   (mod p)
```

and the prover proves `∏ c(reads) − ∏ c(writes) = 0`. By Schwartz–Zippel, if
the two multisets differ, a random choice of `(A0,A1,A2,X)` makes the products
differ except with probability ≤ `(N+T)/p`.

**Toy evaluation** over `p = 101` with `A0=2, A1=3, A2=5, X=7`:

`c = 2·idx + 3·ts + 5·val + 7  (mod 101)`

| triple | computation | `c` |
|:--|:--|:--:|
| `(0,0,4)` | `20+7` | **27** |
| `(1,0,9)` | `2+45+7` | **54** |
| `(0,1,4)` | `3+20+7` | **30** |
| `(1,2,7)` | `2+6+35+7` | **50** |
| `(1,3,7)` | `2+9+35+7` | **53** |
| `(0,4,6)` | `12+30+7` | **49** |

Both lists compress to the same multiset `{27, 54, 30, 50, 53, 49}`, so the
products are automatically equal. Working it out mod 101:

```
27·54 = 1458 ≡ 44
44·30 = 1320 ≡  7
 7·50 =  350 ≡ 47
47·53 = 2491 ≡ 67
67·49 = 3283 ≡ 51
```

`∏ reads = 51`,  `∏ writes = 51`  ⇒  `final_zero = 51 − 51 = 0 (mod 101)`. ✓

---

## 7. Second shuffle — the bound-check set (`diff ∈ {1,…,T}`)

Each access also feeds `diff = newclock − old_ts` into the `InsetZKROM` keyed
on `{1, 2, 3, 4}`. The diffs produced above:

| access | newclock | old_ts | `diff` | in `{1..4}`? |
|:--:|:--:|:--:|:--:|:--:|
| 1 | 1 | 0 | 1 | ✓ |
| 2 | 2 | 0 | 2 | ✓ |
| 3 | 3 | 2 | 1 | ✓ |
| 4 | 4 | 1 | 3 | ✓ |

This is the **second permutation proof**: the set membership check is itself a
ROM-style read≡write shuffle proving every `diff` lies in `{1,…,T}`. It
enforces `old_ts < newclock` (so a read cannot pick up a *future* write) and
that the gap is bounded — the time-ordering that makes the first shuffle sound.

> See **§11** for the full step-by-step procedure of this set, traced on the
> diffs `{1, 2, 1, 3}` above, with its own permutation, product check, and
> soundness argument.

---

## 8. Soundness — two cheats that get caught

### Cheat A — lie about a read value
Suppose at access #3 the prover claims `mem[1] = 8` instead of the true `7`,
i.e. read tuple `(1, 2, 8)`. The committed write tuple `(1, 2, 7)` from access
#2 is unchanged. Now the multisets differ in one element, so the products
diverge. With the same challenge:

- `c(1,2,8) = 2 + 6 + 40 + 7 = 55` replaces `50` on the read side.
- `∏ reads` becomes `100 · 55 = 5500 ≡ 46 (mod 101)` (the other five factors
  multiply to `100`), while `∏ writes` stays `51`.
- `final_zero = 46 − 51 = −5 ≡ 96 ≠ 0` ⇒ **rejected**.

### Cheat B — read from the future / a stale slot
Suppose at access #2 the prover claims `old_ts = 5` while the clock is `2`.
Then `diff = 2 − 5 = −3 ≡ 98 (mod 101)` (in the real field, `p − 3`). Since
`98 ∉ {1,2,3,4}`, the set-membership (second shuffle) fails ⇒ **rejected**.
Equivalently, skipping the latest write leaves it unconsumed, so the final
read picks it up and some intermediate write is never read — breaking the
first shuffle.

---

## 9. ROM gate counts — where `2n + 2T − 2` comes from

The read-only memory (`rom.h`) is the clean case behind the headline
**"2 input gates + 2 multiplication gates per access."** Take the same kind of
example as a ROM: `N` cells, `T` accesses.

**Per-access work (`ZKROM::Access`, rom.h:53):**
- `old_version = IntFp(…, ALICE)` → **1 input**
- `old_val     = IntFp(…, ALICE)` → **1 input**
- `tmp_w.version = old_version + one` → **linear (free)**, no multiplication
- ⇒ **2 inputs, 0 muls per access.**

**Teardown products (`rom.h:104–109`):**
- `prod_read` = product of all `N+T` compressed read terms → `(N+T) − 1` muls
- `prod_write` = product of all `N+T` compressed write terms → `(N+T) − 1` muls

A fan-in-`k` product needs `k − 1` multiplications; here `k = N+T` on each of
two sides:

```
total multiplications = 2·((N+T) − 1) = 2N + 2T − 2
```

That is the `2n + 2T − 2` formula. (The compression `idx·A0 + version·A1 +
val·A2 + X` is all `×public-constant` and `+`, i.e. free; only the running
products cost gates.)

**Input total:** `2T` (accesses) + `2N` (the `N` final reads appended at
teardown, each committing `version` and `val`) `= 2T + 2N`. Setup additionally
commits the `N` initial values once.

**Amortized per access** (divide by `T`):

| quantity | total | per access | limit as `T ≫ n` |
|:--|:--|:--|:--:|
| inputs | `2T + 2n` | `2 + 2n/T` | **2** |
| muls | `2n + 2T − 2` | `2 + (2n − 2)/T` | **2** |

So a toy ROM with `n = 2`, `T = 4` costs exactly `2·2 + 2·4 − 2 = 10`
multiplications and `2·4 + 2·2 = 12` input gates — i.e. `2.5` and `3` per
access — and only converges to the clean `2 + 2` as `T` grows far past `n`
(the `T = ω(n)` assumption from the paper, §2.4 / §4.3).

---

## 10. Per-access cost summary (paper §4.3, amortized, `T ≫ n`)

| structure | input gates / access | mul gates / access |
|:--|:--:|:--:|
| ROM (read-only) | 2 | 2 |
| Set (membership) | 2 | 3 |
| **RAM (read/write)** | **4** | **6** |

The RAM number is the ROM-style read/write core (2 inputs; 2 muls for the two
fan-in products **+ 1** for the `rw` multiplexer in `ram.h:71` = 3 muls)
**plus** the bound-check Set (2 inputs, 3 muls). Two shuffles, constant
overhead per access. The implementation further trims VOLE/mul constants via
the §5.2 optimizations (public set-writes computed in the clear,
`inset_rom.h:101–104`, and the degree-`ε` batched product proof in the
`Teardown_Batch` variants).

---

## 11. Detailed procedure — the bound-check set (`InsetZKROM`)

The set is the **second shuffle**. Its only job: prove that every value the
RAM hands it (`diff = newclock − old_ts`) is a member of `{1, 2, …, total_T}`.
That single fact is what rules out reading from the future or from a stale
slot, which is what makes the *first* shuffle sound.

It is implemented as a tiny **versioned read-only memory** (`inset_rom.h`).
A tuple has only two fields (no value field, i.e. `ℓ = 0`):

```cpp
struct InsetROMTuple { IntFp idx;       // the key
                       IntFp version; } // how many times it has been touched
```

The trick: treat the set `{1,…,M}` as a ROM whose addresses are the set
elements. "Is `x` a member?" becomes "read address `x`." A versioned ROM read
is sound only if address `x` was actually seeded — so a successful read *is* a
membership proof.

In the RAM, `bound_check_rom = InsetZKROM(total_T)` (`ram.h:43`), so its size
is **`M = total_T`** and it is accessed once per RAM access. For our running
example `M = total_T = 4` and it is accessed `T = 4` times with the diffs
`1, 2, 1, 3`.

### 11.1 Setup — seed the keys `{1,…,M}` (`inset_rom.h:43`)

```cpp
for (int i = 1; i <= N; i++) {          // N == M == total_T
    tmp.idx = IntFp(i, PUBLIC);         // key i, public
    tmp.version = IntFp(0, PUBLIC);     // version 0, public
    write_list.push_back(tmp);
    latest_pos.push_back(i-1);          // latest_pos[i] = i-1
}
```

Both fields are **public**, so Setup commits **zero** prover inputs. The
constructor also did `latest_pos.push_back(0)` so slot `0` is an unused dummy
(keys and diffs are ≥ 1).

`write_list` and `latest_pos` after Setup (`M = 4`):

| pos | idx | version | | key | `latest_pos` |
|:--:|:--:|:--:|---|:--:|:--:|
| 0 | 1 | 0 | | 1 | 0 |
| 1 | 2 | 0 | | 2 | 1 |
| 2 | 3 | 0 | | 3 | 2 |
| 3 | 4 | 0 | | 4 | 3 |

### 11.2 Access(diff) — one versioned touch (`inset_rom.h:54`)

```cpp
uint64_t addr = HIGH64(id.value);   // the cleartext diff (prover-side routing)
uint64_t pos  = latest_pos[addr];   // find the latest tuple for key=diff
IntFp old_version = IntFp(HIGH64(write_list[pos].version.value), ALICE); // 1 input
tmp_r = (idx=diff, version=old_version);        // READ the current version
tmp_w = (idx=diff, version=old_version + one);  // WRITE version+1  (linear, free)
read_list.push_back(tmp_r);
write_list.push_back(tmp_w);
latest_pos[addr] = N + T++;          // newest tuple for this key
```

Per access this commits exactly **one** fresh input (`old_version`); the key
`diff` arrives already committed from the RAM (it is the linear combination
`newclock − old_ts`, ram.h:75, which costs no gate), and `version + 1` is
linear. So the version of a key just counts how many times it has been
accessed.

### 11.3 Worked trace on diffs `1, 2, 1, 3`

| set access | diff | `pos=latest_pos[diff]` | old_ver | **read** `(idx,ver)` | **write** `(idx,ver)` | new pos | `latest_pos[diff]` |
|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | 1 | 0 | 0 | `(1, 0)` | `(1, 1)` | 4 | 4 |
| 2 | 2 | 1 | 0 | `(2, 0)` | `(2, 1)` | 5 | 5 |
| 3 | 1 | 4 | 1 | `(1, 1)` | `(1, 2)` | 6 | 6 |
| 4 | 3 | 2 | 0 | `(3, 0)` | `(3, 1)` | 7 | 7 |

Note access #3 reuses key 1: it reads version **1** (left by access #1) and
writes version **2** — the version chain telescopes.

### 11.4 Teardown — final reads + the permutation (`inset_rom.h:69`)

Append one final read of the **latest** version of every key `1…M`:

```cpp
for (int i = 1; i <= N; i++) {
    uint64_t pos = latest_pos[i];
    tmp = (idx=i, version=IntFp(HIGH64(write_list[pos].version.value), ALICE)); // 1 input
    read_list.push_back(tmp);
}
```

| key | `latest_pos[i]` | latest write | final **read** |
|:--:|:--:|:--:|:--:|
| 1 | 6 | `(1, 2)` | `(1, 2)` |
| 2 | 5 | `(2, 1)` | `(2, 1)` |
| 3 | 7 | `(3, 1)` | `(3, 1)` |
| 4 | 3 | `(4, 0)` | `(4, 0)` |

**Complete `write_list`** (`M + T = 8`): seeds + access-writes
`(1,0)(2,0)(3,0)(4,0)` · `(1,1)(2,1)(1,2)(3,1)`
**Complete `read_list`** (`M + T = 8`): access-reads + teardown-reads
`(1,0)(2,0)(1,1)(3,0)` · `(1,2)(2,1)(3,1)(4,0)`

Sort both as `(idx, version)` multisets:

```
both = { (1,0),(1,1),(1,2), (2,0),(2,1), (3,0),(3,1), (4,0) }
```

Identical. ✓ The **second shuffle** holds. Read per key, this is just the
version chain closing up:

| key | versions in writes | versions in reads | accessed? |
|:--:|:--|:--|:--|
| 1 | 0(seed),1,2 | 0,1,2 | twice (#1,#3) |
| 2 | 0(seed),1 | 0,1 | once (#2) |
| 3 | 0(seed),1 | 0,1 | once (#4) |
| 4 | 0(seed) | 0 | never |

### 11.5 The product check, with the public-seed optimization (`inset_rom.h:97`)

Compression uses only two coefficients (no value field):
`c(idx, ver) = A0·idx + A1·ver + X (mod p)`. Reusing `A0=2, A1=3, X=7` over
`p = 101`:

| tuple | `c` | | tuple | `c` |
|:--:|:--:|---|:--:|:--:|
| `(1,0)` | 9  | | `(2,1)` | 14 |
| `(2,0)` | 11 | | `(1,2)` | 15 |
| `(3,0)` | 13 | | `(3,1)` | 16 |
| `(4,0)` | 15 | | `(1,1)` | 12 |

The read side multiplies **all `M+T` committed reads**:

```
∏ reads = 9·11·12·13·15·14·16·15  ≡ 92  (mod 101)
```

The write side uses the **§5.2 optimization**: the `M` seed writes are
`(i, 0)`, fully public, so their product is computed in the clear (no gates,
`inset_rom.h:101–103`) and only the `T` access-writes are committed:

```
acc      = c(1,0)·c(2,0)·c(3,0)·c(4,0) = 9·11·13·15      ≡ 14   (public, in clear)
∏ writes = acc · c(1,1)·c(2,1)·c(1,2)·c(3,1) = 14·(12·14·15·16) ≡ 14·21 ≡ 92
```

`∏ reads = ∏ writes = 92` ⇒ `final_zero = 0`. ✓ (`inset_rom.h:109–110`)

### 11.6 Soundness — a non-member cannot close the shuffle

Suppose the RAM tries a future-read: at access #2 the prover claims
`old_ts = 5` while the clock is `2`, so `diff = 2 − 5 = −3 ≡ p − 3` (in the
toy field, `98`). The set is then Accessed with **key 98**, which was never
seeded:

- The only **version-0** writes in `write_list` are the public seeds
  `(1,0),(2,0),(3,0),(4,0)`. There is no `(98, 0)`, and the prover cannot add
  one (the seeds are public and fixed).
- The teardown final-read loop runs only over keys `1…M`, so key `98` gets no
  closing read either.
- Hence the version-0 read `(98, 0)` the access must produce has **no matching
  write**, and any write `(98, 1)` it produces has **no matching read** — the
  read and write multisets differ.

Concretely, `c(98, 0) = 2·98 + 7 = 203 ≡ 1 (mod 101)`. This factor `1` appears
on the read side but in nothing on the write side, so `∏ reads ≠ ∏ writes` with
overwhelming probability over `A0, A1, X` (Schwartz–Zippel) ⇒ **rejected**.
A negative/out-of-range `diff` simply is not in `{1,…,total_T}`, and the set is
exactly the gadget that detects it.

### 11.7 Cost — 2 inputs + 3 muls per access, and why `M = total_T` matters

This is the one place the "`n` amortizes away" intuition does **not** apply: the
set's size is `M = total_T`, which scales **with** `T`, not below it. Counting
from `Teardown_Basic`:

| | source | count | per access (`M ≈ T`) |
|:--|:--|:--:|:--:|
| **inputs** | Access `old_version` | `T` | 1 |
| | Teardown final-read versions | `M` | 1 |
| | (the key `diff` is free — committed in the RAM) | 0 | 0 |
| | **total** | `M + T ≈ 2T` | **2** |
| **muls** | `∏ reads`, fan-in `M+T ≈ 2T` | `M+T−1` | 2 |
| | `∏ writes` access part (seeds done in clear) | `T` | 1 |
| | **total** | `M + 2T − 1 ≈ 3T` | **3** |

So the bound-check set costs **2 input gates + 3 multiplication gates per
access** — exactly the Set row of §10. Without the §5.2 public-seed
optimization the write product would also pay `M ≈ T` gates, pushing it to
4 muls/access; computing the seed product in the clear is what buys back the
`1`. Added to the read/write core (2 inputs, 3 muls), this gives the RAM its
headline **4 inputs + 6 muls per access**.
