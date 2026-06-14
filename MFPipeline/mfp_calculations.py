
def compute_projections(row,num_weeks,games_counted):
    weeks_left = 10 - num_weeks

    # Compute average score of all weeks
    row['avg_score'] = row[:num_weeks].mean()

    # Number of weeks played
    row['num_games'] = row[:num_weeks].count()

    # Find best five games for a player
    # Updated for Winter22, best six games now
    best_games = [points for points in row[:num_weeks] if points > 0]
    best_games.sort(reverse=True)
    best_games = best_games[:games_counted]

    # Exclude a players
    best_games_aa = [points for points in best_games if points >= row['avg_score']]
    best_games_aa.sort(reverse=True)

    # Attendance totals
    row['avg_att'] = row['num_games'] / num_weeks
    row['proj_att'] = round(row['avg_att'] * 10)
    row['weeks_left_att'] = row['proj_att'] - row['num_games']

    # Total number of points accumulated
    row['cur_total'] = sum([points for points in row[:num_weeks] if points > 0])

    # Find a player's current score, the metric by which players are judged at the end of the season
    row['cur_score'] = sum(best_games)

    # Find a player's current result, the metric used by matchplay to show rank during season (Winter 20, fixed for winter22 change)
    # best (6-weeks_left) scores
    if 6 - weeks_left < 1:
        row['cur_result'] = 0
    else:
        row['cur_result'] = sum(best_games[:6 - weeks_left])

    # mean_adj_score: the points added to a player's projection to supplant their below average games
    # initialize variable to 0 for players that have 5 games above their average

    # If a player has six games above their average, no games are replaced by that average
    if len(best_games_aa) >= 6:
        row['kept_score'] = sum(best_games_aa[:6])
        row['proj_score'] = row['kept_score']
        row['mean_adj_score'] = 0
        row['proj_type'] = 'A'

    # Replace weeks below average with the average score, depending on how many weeks are left
    if len(best_games_aa) < 6:
        row['kept_score'] = sum(best_games_aa)
        if (6 - len(best_games_aa)) <= weeks_left:
            row['mean_adj_score'] = (6 - len(best_games_aa)) * row['avg_score']
            row['proj_type'] = 'B'
        else:
            row['kept_score'] = sum(best_games[:(6 - weeks_left)])
            row['mean_adj_score'] = weeks_left * row['avg_score']
            row['proj_type'] = 'C'
        # Project final score
        row['proj_score'] = row['kept_score'] + row['mean_adj_score']

    # Project attendance and adjust projection
    if len(best_games_aa) < 6:
        row['kept_score_att'] = sum(best_games_aa)
        if (5 - len(best_games_aa) <= row['weeks_left_att']):
            row['mean_adj_score_att'] = (6 - len(best_games_aa)) * row['avg_score']
        else:
            row['kept_score_att'] = sum(best_games[:(6 - int(row['weeks_left_att']))])
            row['mean_adj_score_att'] = int(row['weeks_left_att']) * row['avg_score']
        row['proj_score_att'] = row['kept_score_att'] + row['mean_adj_score_att']
    else:
        row['kept_score_att'] = row['kept_score']
        row['mean_adj_score_att'] = row['mean_adj_score']
        row['proj_score_att'] = row['kept_score_att'] + row['mean_adj_score_att']

    # Find a player's maximum possible score assuming they score a perfect 35 every remaining week
    if weeks_left < 6:
        row['max_score_possible'] = sum(best_games[:6 - weeks_left]) + weeks_left * 35
    else:
        row['max_score_possible'] = 5 * 35

    # The number of weeks of average score added to a player's projection,
    #   so the number of weeks the player would need to do above average to reach their projection
    if row['avg_score'] != 0:
        row['remaining_weeks_above_avg'] = (row['mean_adj_score'] / row['avg_score'])

    # The score a player needs to beat in a future week to improve their score
    # row['score_to_beat'] = best_games[4]
    row['score_to_beat'] = 0
    if len(best_games) == 6:
        row['score_to_beat'] = best_games[-1]

    return row


# calculate the average a player must get in the remaining games to beat the leader
def compute_required_avg_win(row,current_leader,num_weeks):
    weeks_left = 10 - num_weeks
    if row['max_score_possible'] <= current_leader:
        row['required_avg_win'] = 0
    elif row['cur_score'] == current_leader:
        row['required_avg_win'] = 0
    else:
        # Find best five games for a player
        best_games = [points for points in row[:num_weeks] if points > 0]
        best_games.sort(reverse=True)
        best_games = best_games[:5]
        row['required_avg_win'] = ((current_leader + 1) - sum(best_games[:5 - weeks_left])) / weeks_left

    return row


# calculate the average a player must get in the remaining games to beat third place, getting a trophy
def compute_required_avg_trophy(row,current_third,num_weeks):
    #num_weeks = len(row.filter(regex='^[0-9]+$'))
    weeks_left = 10 - num_weeks
    if row['cur_score'] >= current_third:
        row['required_avg_trophy'] = 0
    elif row['max_score_possible'] <= current_third:
        row['required_avg_trophy'] = 0
    else:
        # Find best five games for a player
        best_games = [points for points in row.filter(regex='^[0-9]+$') if points > 0]
        best_games.sort(reverse=True)
        best_games = best_games[:5]
        row['required_avg_trophy'] = ((current_third + 1) - sum(best_games[:6 - weeks_left])) / weeks_left

    return row