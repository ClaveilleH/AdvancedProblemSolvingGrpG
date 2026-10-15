# Variantes écartées (une ligne chacune)

- `t1_sans_remplissage.in` (82 o) : T1 sans requêtes de remplissage ; MOI 1,43e12, autres 1 333 → ratio 1,07e9 fini (écart plus grand, mais ratio < ∞).
- `t1_bornes_officielles_inf.in` (69 o) : T1 avec toutes les valeurs dans les bornes de l'énoncé ; MOI 249, autres 0 → ratio ∞ ; montre que la structure suffit sans grands nombres.
- `t1_bornes_officielles_sans_remplissage.in` (61 o) : idem sans remplissage ; MOI 499 500, autres 1 499 → ratio 333.
- `ff1_fastfill_autre1.in` (55 Ko) : déclenche le fast-fill d'AUTRE_1 (limite de 70 endpoints par cache) ; AUTRE_1 999, les autres 275 279 697 ; ne piège qu'AUTRE_1.
- `t1_principale_113o/` (113 o) : ancienne instance principale (T1, leurre + densité + bug served) ; MOI 1 073 741 822, autres 0 → ratio ∞. **Plus petite instance à ratio ∞**, mais écart deux fois plus faible que T2.
- `t2_sans_remplissage.in` (131 o) : T2 sans remplissage ; MOI 2 147 483 644 666, autres 999 → ratio 2,15e9 fini (meilleur ratio FINI trouvé).
- `r2_m1_principal_fini.in` : R2 avec m = 1 (MOI s'échappe) ; MOI 9,2e11, autres 714 → ratio 1,29e9 fini.
- `ancien_repli_R1/` : ancienne instance de repli (R1, m = 4, 159 o) ; solveur 429 496 729 000, meilleur algo 1 199 → ×3,58e8.
- `repli_R2_k3/` (228 o) : R2 avec 3 lignes de B et A₁ sur 4 lignes ; solveur 920 350 133 510, algos 714 → ×1,29e9 (remplacée par k = 63 : ×2,12e9).
- `r2_m1_k63_sans_recherche_locale.in` (1 963 o) : repli avec une seule petite vidéo ; suffit depuis que la recherche locale de MOI est désactivée (solveur 1 073 741 822 992, algos 507), mais ne piège plus MOI si la recherche locale est réactivée. On garde m = 8, valable dans les deux cas.
- `s1_sur_sans_remplissage.in` (82 o) : T1 sûre (32 bits) sans remplissage ; MOI 715 827 882 000, autres 1 000 → ratio 7,16e8 fini ; identique avec les juges émulés et le scoreur d'AUTRE_1.
