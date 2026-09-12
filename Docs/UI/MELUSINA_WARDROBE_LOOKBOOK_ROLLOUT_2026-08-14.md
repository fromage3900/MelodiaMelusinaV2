# Melusina Wardrobe Browser and Lookbook Rollout

The first UI is a read-model browser over `UMelodiaWardrobeSubsystem`; it must
not become a second mesh or save authority.

## First slice

- `.nikki-outfit-board` visual language and existing CSS assets.
- Grid cards with outfit name, lore excerpt, rarity, owned state, and equipped
  state.
- Equip and unequip actions routed to the wardrobe subsystem.
- Paper-doll preview using the same leader-pose runtime path as gameplay.
- One demo outfit review gate before the 38 gacha records are bulk-registered.

## Data contract

The UI reads catalog records, rarity, ownership, and equipped slot state from
`UMelodiaWardrobeSubsystem`. It uses the existing TokenWallet purchase path and
the v2→v3 save fields. Lore, resonance-quiz, and share-card fields are
presentation extensions and do not change mesh authority.

## Battle safety

Browser equip is presentation/collection behavior while
`bEnableBattleWardrobe` is false. A future owner decision may enable the battle
lane through the explicit T3D gate; no UI action enables it implicitly.
