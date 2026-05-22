# Project Assessment: Senior Tax Exemptions (January 2026)

## Bottom Line

This project area is unlikely to yield a strong paper. Shelving for now.

## The Three Problems

### (a) Not First-Order Economics

The magnitudes are small:
- Florida's property tax exemption: ~$500/year, 0.35% of county levy
- State income tax exemptions: maybe 2-3% of state budgets (needs verification)

Even if we had perfect identification, the findings would be about small effects on small policies. Hard to argue this is where the action is in public finance.

### (b) Not a New Topic

Existing literature already covers the main questions:
- **Do exemptions attract seniors?** Conway & Houtenville (1998), Conway & Rork (2012): No, at least not income tax exemptions.
- **Do seniors respond to property tax exemptions?** Banzhaf et al.: Yes, 32-54% increase in older homeowners.
- **What happens when seniors arrive?** Munoz et al.: Employment multipliers, fiscal revenue gains.
- **How do property taxes affect lifecycle housing?** Coven et al. (2025): Capitalization, senior lock-in, young household crowding out.

Any contribution would be a narrow sub-question. The capitalization test (do Florida exemptions capitalize into prices?) is tractable but not surprising. The budget incidence question (who pays for senior income tax exemptions?) is interesting but faces power and identification problems.

### (c) No Comparative Advantage

I don't have:
- A unique dataset others can't access (Florida data is public)
- A source of policy variation others haven't used (Conway already exploited state-level changes)
- A natural experiment that would crack identification

I *could* try to get something (more granular Florida data, reconstruct Conway's coding, find a sharp policy change), but I haven't convinced myself it's worth the effort given (a) and (b).

## Comparison: What a Good Project Looks Like

Compare to the sportsbook incidence paper (sb_incidence):

| Dimension | Sportsbook | Senior Tax Exemptions |
|-----------|------------|----------------------|
| **Magnitude** | $150B wagered/year, exceeds lotteries | $500/year per household, 0.35% of levy |
| **Policy moment** | States actively debating rates (6.75%-51%), IL just changed | No active policy debate |
| **Unique data** | Odds API, Consumer Edge, Nielsen AdIntel, promo offers | Florida data is public |
| **Surprising finding** | GGR taxes don't pass through (uniform national odds) | Capitalization would be expected |
| **Clean ID** | Illinois excise tax (2024), DMA border design | Within-FL municipal variation (weaker) |
| **Literature gap** | First to use odds data for tax incidence | Conway already covered migration |

The sportsbook paper wasn't even that hard. It just had the right ingredients: big dollars, active policy debate, unique data, clean identification, surprising finding. This project has none of those clearly.

A good paper doesn't require suffering through bad data or weak identification. If the project feels like a slog, that's information.

## What Would Change This Assessment

1. **A large, sharp policy change**: A state dramatically changing senior tax treatment in a way that creates a clean natural experiment.

2. **A first-order reframing**: Finding a way this connects to a bigger question (housing affordability crisis? intergenerational transfers? fiscal federalism?).

3. **A unique dataset**: Something that lets me answer questions others can't—individual-level data on tax-motivated migration, high-frequency budget data around policy changes, etc.

## Files in This Project

- `memos/ourpoint/outline_our_point.tex` - Florida capitalization question (shelved)
- `memos/ourpoint/ourpoint_try2.tex` - Budget incidence question (shelved)
- `memos/ourpoint/brainstorming_our_point.md` - Raw ideas
- `code/florida_analysis/` - Scripts for Florida data (functional but unused)
- `work_log_jan_20_2026.md` - Data discovery session

Florida data request is still pending (emailed Jan 20, 2026). If the data arrives and looks richer than expected, could revisit.

## Decision

Shelve this project. Revisit if: (1) a clear policy shock emerges, (2) the Florida data reveals unexpected variation, or (3) I find a connection to a first-order question.
