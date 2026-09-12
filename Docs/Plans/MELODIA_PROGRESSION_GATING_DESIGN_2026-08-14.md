# Long-term progression + gating — design spec (2026-08-14)

**Spec only. No types, no code.** The wardrobe layers built today
(`FMelodiaResonantForm`, `FMelodiaStyleScore`) are the substrate; this describes the
progression structure that would sit on top, and the three decisions it needs first.

Written after studying how Infinity Nikki structures long-term progression, because
"gated setups for long-term game building" is exactly the problem that game solved and
Melodia currently has no answer for.

---

## 1. The loop worth stealing (structure, not content)

Infinity Nikki's endgame is a **self-reinforcing exploration loop**:

```
explore  ->  collect Whimstars  ->  spend them in the Heart of Infinity tree
         ->  unlock an Ability Outfit  ->  that ability reaches Whimstars you could not
         ->  explore further
```

The parts that make it work:

| Element | Detail |
|---|---|
| **Collectible** | 366 Whimstars. **Tiered acquisition**: some you walk up to, some need a challenge, some need an Ability Outfit you do not have yet |
| **Tree** | Sequential — slots cannot be skipped. Reaching a leaf means unlocking every node before it |
| **Shards** | Three parallel trees, each region-themed, each featuring its own Miracle Outfits |
| **Region-scoped currency** | Whimstar (Wishfield), Whimstar (Itzaland), Ethereal Stars — a region's collectibles feed that region's tree |
| **Reward** | Tree nodes grant **Ability Outfit sketches** — the outfit IS the ability |

**The load-bearing part is the third acquisition tier.** Collectibles that *require an ability
you do not yet have* are what turn a checklist into a loop. Without them you get a
collectathon; with them, every new ability retroactively opens the whole map.

## 2. What Melodia already has

More than it looks:

| Nikki concept | Melodia equivalent | State |
|---|---|---|
| Ability Outfit | `FMelodiaResonantForm` + a cosmetic pointing at it | **Built today**, uncompiled-to-tested |
| Ability that gates traversal | `EMelodiaFormCapability { Glide, Dash, Swim }` | Source-wired through the module-neutral capability registry; closed-editor build and live evidence pending |
| Unlock gate | `FMelodiaResonantForm::RequiredFlagIds` | Built — but **binary**, see §3 |
| Region restriction | `RestrictedContextIds` | Built |
| Shard / region theming | `content_pack_id` — `Core`, `Pack_MoonlitSonata`, `Pack_GildedOverture` | **Exists in drafts, unmodelled in C++** |
| Currency | `UMelodiaTokenWalletSubsystem::GoldenTokens` | Built, and the audit called it the **cleanest** system here |
| Collectible | — | **Nothing.** This is the actual gap |

So the missing pieces are a **collectible**, a **tree**, and the **traversal wiring** that makes
abilities matter.

## 3. The one structural change the current design needs

`RequiredFlagIds` is a **binary** gate: all flags true, or locked. That models "the story
reached a point". It cannot model "you spent 8 of 12 collectibles toward this".

A progression tree needs two things the form layer lacks:

1. **A cost** — how much of what is spent to unlock this node.
2. **Prerequisite nodes** — which node(s) must already be unlocked.

**Recommendation: do not put these on `FMelodiaResonantForm`.** Keep the form describing
*what an ability is and when it is suppressed*, and put cost/prerequisite on a separate
progression-node type that *references* a form id. Same separation that already keeps
cosmetics from carrying capabilities — and for the same reason: several nodes may eventually
grant the same form, and a form should be authorable before any tree exists.

## 4. ~~The currency question~~ — already solved in code

**Owner, 2026-08-14: one wallet, the Melody Token wallet.** This section previously called the
currency question "a trap" and recommended building "one collectible type, region-*tagged* rather
than region-*typed*". **That already exists** — I recommended building something shipped.

`UMelodiaTokenWalletSubsystem` holds:

```
TMap<FName,int32> Shards      keyed by element: Forte, Tide, Gale, Stone, Radiant, Umbral, Arcane
float             ManaCurrent / ManaMax
int32             GoldenTokens, TotalCollected
GetShards(Element) · TryGrantShards(Element, Amount, GrantId) · TrySpendShards(Element, Amount)
```

Element-tagged, single authority, one changed-event, persisted through the canonical save record.
`TryGrantShards` already takes a **`GrantId` for duplicate rejection** — exactly the idempotency a
world collectible needs, so a pickup cannot double-grant on save/reload.

`{heart, swirl}` in the cosmetic drafts were never a second currency: they are token **art
variants** mapping to Forte/Arcane shards via `Content/Python/gmm/game/tokens.py`.

**So the progression gap shrinks to two things**, and neither is an economy decision:

1. A **collectible actor** that calls `TryGrantShards(Element, Amount, GrantId)`.
2. A **tree node type** that spends via `TrySpendShards` and gates on prerequisites.

The element vocabulary is now consistent in three places — `EMelodiaSpellElement` (skills, enemies,
weakness keys), wallet shards (economy), and `FMelodiaStyleScore::Element` (styling). A Tide-strong
outfit, a Tide harmonic key, and a Tide shard speak one language. That coherence is worth
protecting: **do not introduce a progression currency outside the wallet.**

**Carry this risk:** the wallet header states there is **no runtime GMM↔Unreal channel**. It is a
parallel implementation of `gmm/game/tokens.py`, kept honest only by matching test expectations
(`Content/Python/gmm/tests/test_tokens.py`). Two implementations of one economy, no automated
cross-check.

## 5. Melodia-native framing

The mechanics transfer; the fiction should not. Nikki's tree is *Heart of Infinity*, its
collectibles are *Whimstars*, its rewards are *Miracle Outfits*.

Melodia's vocabulary is musical and **already established in code** — `EMelodiaSpellElement`
gives seven harmonic elements (Forte, Tide, Gale, Stone, Radiant, Umbral, Arcane), and the
content packs are already named as musical forms (*Moonlit Sonata*, *Gilded Overture*).

That suggests the natural shape without inventing anything: **a tree per harmonic element or
per movement**, collectibles that are fragments of a score, and Resonant Forms as the leaves.
The four-movement north star in the long-term plan is a better fit for "Shards" than an
invented region split.

**Do not name any of this until the mechanics are decided.** Naming first is how a system ends
up shaped by its metaphor.

## 6. What blocks starting

Three decisions, all already open, all now with more riding on them:

1. **Traversal baseline** — do Resonant Forms *add* capabilities to a baseline, or *are* they
   the only source? **This one gates the whole design.** A forms-only model makes the tree the
   spine of the game; a baseline-plus model makes it optional enrichment. They are different
   games and the tree cannot be designed without the answer.
2. ~~Currency~~ — **RESOLVED 2026-08-14**, see §4. One Melody Token wallet, element-keyed shards,
   already implemented.
3. **Rarity ladder** — lower stakes here, but it will govern what tree nodes cost.

## 7. Suggested build order, once decided

1. Compile and live-verify the module-neutral registry path from
   `UMelodiaTraversalComponent` to the Wardrobe capability provider — this makes the
   abilities *mean* something. Nothing else is worth building first.
2. One collectible actor + its record field on `FMelodiaNarrativeRecord` (**not** a new save).
3. One tree node type, referencing a form id, with cost and prerequisites.
4. One authored branch, end to end: collect → spend → unlock a form → that form reaches a
   collectible that was unreachable. **The loop closing once is the proof; scale after.**
5. Only then, `content_pack_id` as the Shard grouping and a collection album on top.

## 8. Deliberately not decided here

Node counts, costs, curve, how many collectibles, how many trees, what anything is called.
Those are balance and fiction, and they need the mechanics settled and one branch playable
before they mean anything.

**Sources studied:** [Heart of Infinity guide](https://game8.co/games/Infinity-Nikki/archives/487217),
[Heart of Infinity wiki](https://infinity-nikki.fandom.com/wiki/Heart_of_Infinity),
[what Whimstars are used for](https://gamerant.com/infinity-nikki-what-are-whimstars-used-for/),
[Whimstar challenge types](https://www.thegamer.com/infinity-nikki-whimstar-challenges-ranked/),
[skills and insights](https://www.thegamer.com/infinity-nikki-insight-skills-animal-bug-fishing-collect-heart/).
