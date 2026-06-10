"""
Seed data for the knowledge base.
Run this script to populate the SQLite DB with initial domain knowledge.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from modules.knowledge_base import init_db, _get_conn


def seed():
    """Populate all KB tables with initial data."""
    init_db()
    conn = _get_conn()
    cur = conn.cursor()

    # -----------------------------------------------------------------------
    # BETTING STRATEGIES
    # -----------------------------------------------------------------------
    strategies = [
        ("Value Betting", "Identifying bets where the bookmaker's odds imply a lower probability than your own assessment. You bet when you believe the true probability of an outcome is higher than what the odds suggest.", "medium", "core",
         "If a bookmaker offers odds of 3.00 (implied prob 33%) on Team A winning, but your analysis suggests Team A has a 40% chance, that's a value bet."),
        ("Matched Betting", "Using free bet promotions and bonuses from bookmakers to cover all outcomes of an event, guaranteeing a profit regardless of the result.", "low", "arbitrage",
         "Bookmaker offers a $50 free bet. You place the free bet on one outcome and lay it on a betting exchange, locking in profit."),
        ("Arbitrage Betting", "Exploiting differences in odds between multiple bookmakers to place bets on all possible outcomes, ensuring a guaranteed profit.", "low", "arbitrage",
         "Bookmaker A offers 2.10 on Home Win, Bookmaker B offers 2.10 on Away Win. By splitting your stake correctly, you profit regardless."),
        ("Over/Under Goals", "Betting on whether the total number of goals in a match will be over or under a specified threshold (usually 2.5).", "medium", "market_type",
         "If two attacking teams with poor defenses play, Over 2.5 goals might be a good bet. Check average goals per game for both teams."),
        ("Asian Handicap", "A form of spread betting that eliminates the draw outcome by giving one team a virtual advantage or disadvantage.", "medium", "market_type",
         "Team A -1.5 Asian Handicap: Team A must win by 2+ goals for the bet to win. If they win by 1, you lose."),
        ("Double Chance", "Betting on two of three possible outcomes (1X, X2, 12). Lower odds but higher probability of winning.", "low", "market_type",
         "If you think the home team won't lose, bet on '1X' (Home Win or Draw). Safer but lower returns."),
        ("Both Teams to Score (BTTS)", "Betting on whether both teams will score at least one goal during the match.", "medium", "market_type",
         "Check both teams' scoring record and clean sheet stats. Teams that score often but defend poorly are ideal for BTTS: Yes."),
        ("Accumulator (Parlay)", "Combining multiple selections into a single bet. All selections must win for the bet to pay out, but returns are multiplied.", "high", "bet_type",
         "Combining 4 match results at odds of 1.50 each: 1.50 × 1.50 × 1.50 × 1.50 = 5.06 total odds. High risk, high reward."),
        ("In-Play Betting", "Placing bets during a live match based on the current state of play, momentum, and tactical changes.", "high", "timing",
         "If a strong team goes down 0-1 early, odds for them to win increase significantly. If their form suggests a comeback, this can be value."),
        ("Draw No Bet (DNB)", "Betting on a team to win with insurance — if the match ends in a draw, your stake is refunded.", "low", "market_type",
         "Similar to Asian Handicap 0. Useful for matches where you think a team will likely win but want draw protection."),
        ("Correct Score", "Predicting the exact final score of a match. Very difficult but offers high odds.", "high", "market_type",
         "Predict 2-1 Home Win. Check historical H2H scores, average goals, and defensive records to make an informed guess."),
        ("Half-Time/Full-Time", "Predicting the result at both half-time and full-time. Offers good odds due to difficulty.", "high", "market_type",
         "Bet on Draw/Home Win if you expect a team to start slow but dominate the second half."),
        ("Form-Based Betting", "Analyzing recent results (last 5-10 matches) to identify teams on winning/losing streaks and betting accordingly.", "medium", "analytical",
         "A team winning 8 of last 10 matches is in great form. But check the quality of opponents they faced."),
        ("Head-to-Head Analysis", "Using historical match data between two teams to identify patterns and tendencies.", "medium", "analytical",
         "If Team A has beaten Team B in 7 of the last 10 meetings, this historical dominance is a strong factor."),
        ("Bankroll Management — Flat Staking", "Betting a fixed percentage (1-5%) of your total bankroll on each bet. Prevents emotional betting and protects against losing streaks.", "low", "money_management",
         "With a $1000 bankroll and 2% flat stake, each bet is $20 regardless of confidence level. Professional bettors rarely exceed 5%."),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO betting_strategies (name, description, risk_level, category, example) VALUES (?, ?, ?, ?, ?)",
        strategies
    )

    # -----------------------------------------------------------------------
    # BETTING TERMS
    # -----------------------------------------------------------------------
    terms = [
        ("Odds", "The numerical expression of the likelihood of an outcome, which also determines potential payout. Can be expressed as decimal (2.50), fractional (3/2), or American (+150).", "If a team has decimal odds of 2.50, a $10 bet returns $25 (including your stake).", "basics"),
        ("Stake", "The amount of money placed on a bet.", "I placed a $20 stake on Liverpool to win.", "basics"),
        ("Bankroll", "The total amount of money a bettor has set aside specifically for betting.", "My betting bankroll is $500. I never bet more than 2% per match.", "money_management"),
        ("Accumulator", "A single bet that combines multiple selections. All must win for the bet to succeed.", "My 5-fold accumulator paid out at 12.0 odds!", "bet_types"),
        ("Handicap", "A virtual advantage or disadvantage given to a team to level the playing field in betting.", "Man City -1.5 handicap means they need to win by 2 or more goals.", "bet_types"),
        ("Over/Under", "A bet on whether a specific statistic (usually goals) will be over or under a set number.", "Over 2.5 goals means 3 or more goals must be scored in the match.", "bet_types"),
        ("Clean Sheet", "When a team does not concede any goals during a match.", "Liverpool kept a clean sheet, winning 2-0.", "football"),
        ("Form", "A team's recent results, typically measured over the last 5-6 matches.", "Arsenal are in great form — WWWDW in their last 5.", "football"),
        ("Head-to-Head (H2H)", "Historical record of results between two specific teams.", "The H2H record shows Barcelona have won 6 of the last 10 El Clásicos.", "football"),
        ("Expected Value (EV)", "A mathematical calculation showing the average amount you can expect to win or lose per bet over time.", "+EV means the bet is profitable long-term. EV = (Prob × Payout) - Stake.", "advanced"),
        ("Implied Probability", "The probability of an outcome as suggested by the bookmaker's odds.", "Odds of 2.00 = 50% implied probability. Odds of 4.00 = 25% implied probability.", "advanced"),
        ("Closing Line Value (CLV)", "The difference between the odds you took and the final odds at kickoff. Consistently beating the closing line indicates good betting skill.", "If you bet at 2.50 and the closing line was 2.20, you had positive CLV.", "advanced"),
        ("Push", "When the result exactly matches the spread/total, resulting in the bet being voided and the stake returned.", "If the line is Over 2.0 goals and exactly 2 goals are scored, it's a push.", "bet_types"),
        ("Juice (Vig/Vigorish)", "The bookmaker's commission built into the odds. It's how they guarantee profit.", "True 50/50 odds would be 2.00, but bookmakers offer 1.91 on each side — the difference is the juice.", "advanced"),
        ("Lay Bet", "Betting against an outcome on a betting exchange. You act as the bookmaker.", "I laid a bet on Chelsea to win, meaning I profit if Chelsea draw or lose.", "bet_types"),
        ("Treble", "An accumulator bet with exactly three selections.", "My treble of Liverpool, Real Madrid, and Bayern all came through!", "bet_types"),
        ("Each-Way", "A bet consisting of two parts: one on the selection to win and one on it to place.", "Mostly used in horse racing, but the concept applies to tournament outright bets.", "bet_types"),
        ("Cash Out", "An option offered by bookmakers to settle a bet before the event ends, locking in profit or cutting losses.", "My accumulator had 4 of 5 legs won. I cashed out early for guaranteed profit.", "basics"),
        ("Dead Heat", "When two or more selections tie in a market, the stake is divided proportionally.", "Two players tied for top scorer, so my bet was settled at half odds.", "advanced"),
        ("Dutching", "Spreading your stake across multiple selections in the same market to ensure profit regardless of which one wins.", "In a 3-horse race, you can dutch the top 2 favorites to guarantee profit if either wins.", "strategy"),
        ("Ante-Post", "A bet placed well in advance of an event, often at enhanced odds.", "Ante-post bets on the Premier League winner are available before the season starts.", "bet_types"),
        ("In-Play / Live Betting", "Betting on events after they have started, with odds updating in real-time.", "I waited until halftime to place my in-play bet when the odds were better.", "bet_types"),
        ("Moneyline", "A straight bet on which team will win, with no spread involved.", "The moneyline on Barcelona is -200 (American odds) to win.", "bet_types"),
        ("Spread", "A margin of victory set by bookmakers. The favorite must win by more than the spread.", "If the spread is -2.5 for Man City, they must win by 3+ goals to cover.", "bet_types"),
        ("Unit", "A standard measurement of bet size, typically 1% of your bankroll.", "I bet 2 units on this match — that's 2% of my bankroll.", "money_management"),
        ("ROI (Return on Investment)", "A percentage showing total profit relative to total amount staked.", "My ROI this season is +8%, meaning I've profited $8 for every $100 staked.", "money_management"),
        ("Tipster", "A person who provides betting tips and predictions, often for a fee.", "I follow a football tipster who specializes in the Bundesliga.", "basics"),
        ("Bookmaker (Bookie)", "A company or individual that accepts bets on sporting events and sets the odds.", "Popular bookmakers include Bet365, William Hill, and Unibet.", "basics"),
        ("Handicap (Asian)", "A handicap system that uses quarter-goal increments and can split stakes between two handicap lines.", "Team A -0.75 means half your stake goes on -0.5 and half on -1.0.", "bet_types"),
        ("Outright", "A bet on the overall winner of a tournament or league, rather than an individual match.", "I placed an outright bet on Real Madrid to win the Champions League.", "bet_types"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO betting_terms (term, definition, example_usage, category) VALUES (?, ?, ?, ?)",
        terms
    )

    # -----------------------------------------------------------------------
    # LEAGUE INSIGHTS
    # -----------------------------------------------------------------------
    league_insights = [
        ("Premier League", "Most-watched league globally. High competitiveness with 6+ title contenders. Average 2.7 goals per game. Strong home advantage historically.", "Increasing dominance of top 4 clubs in revenue. Mid-table teams improving through investment. High managerial turnover.", "Consider BTTS in matches involving mid-table teams. Draw rate ~25%. Underdogs often competitive. Look for value in away wins of top teams at promoted sides."),
        ("La Liga", "Historically dominated by Real Madrid and Barcelona. Technical, possession-based football. Average 2.5 goals per game.", "Growing parity as Atletico, Real Sociedad, and Athletic compete. Lower-budget clubs often park the bus against top teams.", "Under 2.5 goals is common in matches involving Atletico Madrid. Real Madrid and Barcelona cover Asian Handicaps frequently at home."),
        ("Bundesliga", "Highest average attendance in world football. Bayern Munich dominance (11+ consecutive titles). Average 3.1 goals per game — highest of top 5 leagues.", "Most open and attacking league. Dortmund as perennial challengers. Strong youth development across clubs.", "Over 2.5 goals hits frequently. Bayern Munich rarely drops points at home. Promoted teams often struggle in first season."),
        ("Serie A", "Traditionally defensive and tactical. Average 2.6 goals per game. Strong home advantage.", "Increasing investment from foreign owners. Inter and Napoli emerging as strongest challengers. Juventus in rebuilding phase.", "Under 2.5 in matches involving defensively solid teams (Juventus, Napoli). Home advantage is significant — consider 1X in home matches."),
        ("Ligue 1", "PSG dominance (9 of last 12 titles). Average 2.6 goals per game. Competitive mid-table.", "Financial Fair Play impacting PSG. Monaco, Marseille, and Lyon as main challengers. Strong talent production pipeline.", "PSG cover large handicaps at home. Draw rate is lower in PSG matches. Look for value in mid-table clashes."),
        ("Champions League", "Elite European club competition. Two-leg knockout rounds from Round of 16. Group stage ensures minimum 6 matches.", "New 36-team league format from 2024/25. More matches, more variance. Home advantage less pronounced than domestic leagues.", "First legs tend to be cagey (Under 2.5). Big clubs rarely lose at home in group stage. Knockout rounds: expect tight, tactical affairs."),
        ("Eredivisie", "Offensive, open football. Average 3.2 goals per game. Ajax, PSV, and Feyenoord dominate.", "High goal-scoring league with young talent. Large gap between top 3 and rest. Many goals from set pieces.", "Over 2.5 goals is very reliable. BTTS hits frequently. Top 3 teams cover handicaps against bottom half."),
        ("Primeira Liga", "Dominated by Benfica, Porto, and Sporting. Technical football with lower tempo. Average 2.4 goals per game.", "The big 3 account for vast majority of titles. Other teams rarely cause upsets. Strong feeder league for top 5 leagues.", "Home wins are very common. Under 2.5 in matches between big 3 and lower-half teams. Outright market is usually a 3-horse race."),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO league_insights (league_name, key_stats, trends, betting_tips) VALUES (?, ?, ?, ?)",
        league_insights
    )

    # -----------------------------------------------------------------------
    # FAQ
    # -----------------------------------------------------------------------
    faqs = [
        ("How do I convert decimal odds to implied probability?", "Divide 1 by the decimal odds and multiply by 100. Example: Odds of 2.50 → 1/2.50 × 100 = 40% implied probability.", "odds"),
        ("What is the best bankroll management strategy?", "The flat staking method is recommended for beginners: bet 1-3% of your bankroll on each bet. Never chase losses. Set a daily/weekly loss limit and stick to it.", "money_management"),
        ("How do I identify value bets?", "Compare your own probability assessment with the bookmaker's implied probability. If you estimate a team has a 50% chance of winning but odds imply only 40%, that's a value bet (positive expected value).", "strategy"),
        ("What does '+EV' mean?", "+EV stands for 'positive Expected Value'. It means a bet is profitable in the long run. EV = (Probability of Winning × Payout) – (Probability of Losing × Stake). If EV > 0, the bet has positive expected value.", "advanced"),
        ("Should I follow tipsters?", "Be cautious. Verify a tipster's track record (minimum 500+ bets). Look for transparency in results, including losing bets. Good tipsters focus on ROI and yield, not win rate alone. Never pay for tips without a verified history.", "general"),
        ("What is the safest type of bet?", "Double Chance (1X, X2, 12) and Draw No Bet are the safest single-match bet types, as they cover two outcomes. However, 'safe' bets have lower odds and may not always offer value.", "strategy"),
        ("How many bets should I place per day?", "Quality over quantity. Professional bettors typically place 1-5 bets per day, focusing only on matches where they've found value. Avoid betting on every match — selectivity is key.", "money_management"),
        ("What is line shopping?", "Comparing odds across multiple bookmakers to find the best price for your bet. Even small differences (e.g., 1.90 vs 1.95) compound significantly over hundreds of bets.", "strategy"),
        ("Is it better to bet pre-match or in-play?", "Both have advantages. Pre-match is better for well-researched bets. In-play offers opportunities to assess team performance and find value after kickoff. Experienced bettors use both.", "strategy"),
        ("How do I read a league standings table?", "Key columns: P (Played), W (Won), D (Drawn), L (Lost), GF (Goals For), GA (Goals Against), GD (Goal Difference), Pts (Points). Points = 3 per win, 1 per draw. Teams are ranked by points, then goal difference.", "basics"),
        ("What is a correct score refund?", "Some bookmakers offer a refund (as a free bet) if the match ends 0-0 and you bet on a different correct score. It's a promotional offer, not a standard bet type.", "basics"),
        ("How do I calculate parlay/accumulator odds?", "Multiply the decimal odds of all selections together. Example: 1.50 × 2.00 × 1.80 = 5.40. A $10 bet would return $54. Remember: the more selections, the lower the probability of winning.", "odds"),
        ("What does 'hedging a bet' mean?", "Placing a second bet on the opposite outcome to guarantee a profit or minimize losses. Often used when an accumulator has one leg remaining.", "strategy"),
        ("How important is home advantage?", "Very important. Historically, home teams win ~45% of matches across top leagues, with ~27% draws and ~28% away wins. However, this advantage has decreased since COVID (empty stadiums era).", "football"),
        ("What are the most common football scores?", "The most common scorelines in top leagues are: 1-0 (~13%), 1-1 (~11%), 2-1 (~10%), 2-0 (~9%), 0-0 (~8%). Knowing these helps with correct score bets.", "football"),
        ("Should I bet on my favorite team?", "Generally no. Emotional bias leads to overestimating your team's chances. If you do, be extra critical in your analysis and consider skipping matches where you can't be objective.", "general"),
        ("What is Expected Goals (xG)?", "A statistical metric that measures the quality of goal-scoring chances. Each shot is assigned a probability based on factors like distance, angle, and assist type. Higher xG means better chances created.", "advanced"),
        ("How do bookmakers set odds?", "Bookmakers use statistical models, team news, historical data, and market demand. They set odds to attract balanced action on both sides and build in a margin (overround/vig) to ensure profit.", "basics"),
        ("What is a betting exchange?", "A platform where bettors bet against each other rather than against a bookmaker. You can 'back' (bet for) or 'lay' (bet against) outcomes. Exchanges charge a commission on winnings. Examples: Betfair, Smarkets.", "basics"),
        ("How do I track my betting performance?", "Record every bet: date, match, market, odds, stake, and result. Calculate your ROI (total profit / total staked × 100) and yield. Use a spreadsheet or dedicated tracking app. Minimum 200+ bets for meaningful analysis.", "money_management"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO faq (question, answer, category) VALUES (?, ?, ?)",
        faqs
    )

    # -----------------------------------------------------------------------
    # TEAM ANALYSIS NOTES (example entries)
    # -----------------------------------------------------------------------
    team_notes = [
        ("Manchester City", "Premier League", "2024/25", "Exceptional squad depth, dominant ball possession, world-class midfield (Rodri, De Bruyne). Strong in both domestic and European competitions.", "Aging squad, occasional defensive vulnerabilities without key players. Can struggle against high-pressing teams.", "Consistent top performers. Strong at home, rarely drop points at Etihad."),
        ("Real Madrid", "La Liga", "2024/25", "Incredible winning mentality, strong in big matches. Elite attack with Vinicius Jr and Mbappé. Historically dominant in Champions League.", "Can be vulnerable to counter-attacks. Midfield transition period after Kroos retirement.", "Dominant at Santiago Bernabéu. Tend to peak in the second half of the season."),
        ("Bayern Munich", "Bundesliga", "2024/25", "Strongest squad in German football. High-pressing style creates many chances. Excellent academy production.", "Occasional defensive lapses in transition. Can struggle in Champions League knockout rounds against tactical teams.", "Near-perfect home record. Cover large handicaps against lower Bundesliga teams."),
        ("Liverpool", "Premier League", "2024/25", "High-energy pressing style. Strong attacking trio. Excellent home record at Anfield.", "Can be exposed on counter-attacks when pushing forward. Injuries to key players significantly impact performance.", "Anfield is a fortress. Strong in first halves. Often involved in high-scoring matches."),
        ("Barcelona", "La Liga", "2024/25", "Exciting young squad (Yamal, Pedri). Possession-based philosophy. Strong La Masia integration.", "Financial constraints limiting transfers. Can struggle in away European matches against physical teams.", "Strong home record at Camp Nou. Young squad means occasional inconsistency."),
        ("Arsenal", "Premier League", "2024/25", "Excellent defensive organization under Arteta. Strong set-piece threat. Growing squad depth.", "Can lack creativity against deep defensive blocks. Relatively thin squad compared to Man City.", "Very strong at home. Title contenders with improving consistency."),
        ("Inter Milan", "Serie A", "2024/25", "Strongest squad in Italian football. Excellent tactically under Inzaghi. Strong in both attack and defense.", "Fixture congestion can affect performance. Aging key players.", "Dominant domestically. Strong in big matches. Good at covering handicaps."),
        ("PSG", "Ligue 1", "2024/25", "Massive financial power. Domestic dominance. Star-studded squad.", "Champions League struggles continue. Over-reliance on individual brilliance over team cohesion.", "Cover huge handicaps in Ligue 1. Home record is near-perfect. European away form is inconsistent."),
        ("Atletico Madrid", "La Liga", "2024/25", "Best defensive organization in Spain. Strong mentality in knockout competitions. Excellent counter-attacking.", "Can be frustrating to watch due to defensive style. Goal-scoring can dry up without Griezmann's creativity.", "Under 2.5 goals is common in their matches. Rarely lose at home. Strong in Champions League group stages."),
        ("Borussia Dortmund", "Bundesliga", "2024/25", "Exciting attacking football. Electric atmosphere at Signal Iduna Park (Yellow Wall). Strong youth development.", "Inconsistency in away matches. Defensive fragility at times.", "High-scoring matches. Over 2.5 goals very common. Home advantage is massive."),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO team_analysis_notes (team_name, league, season, strengths, weaknesses, form_notes) VALUES (?, ?, ?, ?, ?, ?)",
        team_notes
    )

    # -----------------------------------------------------------------------
    # HISTORICAL TIPS (examples)
    # -----------------------------------------------------------------------
    historical_tips = [
        ("Manchester City vs Arsenal – Premier League", "Over 2.5 Goals", "Both teams are attack-minded. Recent H2H shows 3+ goals in 7 of last 10. High-stakes match increases attacking intent.", "Won (3-1)", 1.85),
        ("Barcelona vs Real Madrid – La Liga (El Clásico)", "BTTS: Yes", "Both teams have elite attacking talent. El Clásico historically produces goals from both sides.", "Won (2-3)", 1.65),
        ("Bayern Munich vs Dortmund – Bundesliga (Der Klassiker)", "Over 3.5 Goals", "Bundesliga's two most attacking teams. Average 4.2 goals in last 10 meetings.", "Won (4-2)", 2.10),
        ("Liverpool vs Manchester United – Premier League", "Liverpool Win & Over 1.5 Goals", "Liverpool dominant at Anfield vs United in recent years. 5 wins in last 6 home meetings.", "Won (3-0)", 1.75),
        ("Atletico Madrid vs Sevilla – La Liga", "Under 2.5 Goals", "Atletico's defensive style limits goals. 8 of last 10 H2H had under 2.5 goals.", "Won (1-0)", 1.70),
        ("PSG vs Marseille – Ligue 1 (Le Classique)", "PSG Win -1.5 Asian Handicap", "PSG's dominance at home in this fixture. Won last 5 home meetings by 2+ goals.", "Won (3-0)", 1.90),
        ("Inter Milan vs AC Milan – Serie A (Derby della Madonnina)", "BTTS: Yes + Over 2.5", "Milan derbies are heated and open. Last 8 derbies had 3+ goals and both teams scoring.", "Lost (1-0)", 2.20),
        ("Ajax vs Feyenoord – Eredivisie (De Klassieker)", "Over 3.5 Goals", "Dutch football = goals. Classic rivalry with attacking intent from both sides.", "Won (4-3)", 2.00),
        ("Juventus vs Napoli – Serie A", "Draw", "Tactical, tight affair expected. 4 draws in last 10 meetings. Both teams cautious.", "Lost (1-2)", 3.40),
        ("Real Madrid vs Manchester City – Champions League", "BTTS: Yes", "Two attacking powerhouses. Last 4 meetings all had both teams scoring.", "Won (3-2)", 1.55),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO historical_tips (match_description, prediction, reasoning, result, odds_taken) VALUES (?, ?, ?, ?, ?)",
        historical_tips
    )

    conn.commit()
    conn.close()
    print("✅ Knowledge base seeded successfully!")


if __name__ == "__main__":
    seed()
