import pandas as pd
import requests
from dagster import job, op, Out, In, get_dagster_logger
from mfp_calculations import compute_projections, compute_required_avg_win, compute_required_avg_trophy


@op(config_schema={"series_id": str})
def scrape_matchplay(context):
    series_url = 'https://matchplay.events/data/series/' + context.op_config["series_id"] + '/standings'
    return requests.get(series_url).json()['tournament_points']


@op
def clean_matchplay_data(data):
    data = [{**x, **x.pop('points')} for x in data]
    df = pd.DataFrame(data).transpose().reset_index()
    df.columns = df.loc[0]
    df.rename(columns={'tournament_id': 'player_id'}, inplace=True)
    df = df.iloc[2:]
    df = df.set_index('player_id')
    return df


@op
def find_player_names(points_df):
    # Url to grab weekly standings for names
    tournament_ids = points_df.columns
    tournament_url_a = 'https://matchplay.events/data/tournaments/'
    tournament_url_b = '/standings'

    player_names = {}
    for tournament_id in tournament_ids:
        tournament_url = tournament_url_a + str(tournament_id) + tournament_url_b
        r = requests.get(tournament_url)
        data = r.json()
        for player in data:
            if player['player_id'] not in player_names:
                player_names[str(player['player_id'])] = player['name']
    points_df.index = points_df.index.map(player_names)
    return points_df


@op(config_schema={"tournaments_counted": int},
    out={"df_with_projections": Out(), "num_weeks": Out()})
def calculate_series_projections(context, points_df):
    num_weeks = points_df.shape[1]
    get_dagster_logger().info(f"Number of tournaments played in series: {num_weeks}")
    games_counted = context.op_config['tournaments_counted']
    final_points_df = points_df.apply(compute_projections, num_weeks=num_weeks, games_counted=games_counted, axis=1)
    final_points_df.sort_values('proj_score', ascending=False, inplace=True)
    return final_points_df, num_weeks


@op(out={"points_df":Out(),"num_weeks":Out()})
def calculate_required_avg_to_win(df_with_projections, num_weeks):
    # df = df_with_projections
    # num_weeks = df[df.columns.drop(list(df.filter(regex='^[0-9]+$')))].shape[1]
    current_leader = df_with_projections['cur_score'].max()
    points_df = df_with_projections.apply(compute_required_avg_win, current_leader=current_leader, num_weeks=num_weeks,
                                          axis=1)
    points_df['score_rank'] = points_df.cur_score.rank(method='first', ascending=False)
    return points_df, num_weeks


@op
def calculate_required_avg_trophy(points_df, num_weeks):
    # df = points_df
    # num_weeks = df[df.columns.drop(list(df.filter(regex='^[0-9]+$')))].shape[1]
    current_third = points_df[points_df.score_rank == 3].cur_score[0]
    points_df = points_df.apply(compute_required_avg_trophy, current_third=current_third, num_weeks=num_weeks, axis=1)
    return points_df


@op
def export_to_csv(final_points_df):
    final_points_df.to_csv('test.csv')


@op
def display_df(points_df):
    return points_df


@job
def pull_and_project():
    data = scrape_matchplay()
    points_df, num_weeks = calculate_series_projections(find_player_names(clean_matchplay_data(data)))
    points_df, num_weeks = calculate_required_avg_to_win(points_df, num_weeks)
    final_points_df = calculate_required_avg_trophy(points_df, num_weeks)
    export_to_csv(final_points_df)
    display_df(final_points_df)


if __name__ == "__main__":
    # start_run_config_marker
    run_config = {
        "ops": {
            "scrape_matchplay": {
                "config": {"series_id": "1875"}}
        }
    }
    # end_run_config_marker
    # start_execute_marker
    result = pull_and_project.execute_in_process(run_config=run_config)
    # end_execute_marker
    assert result.success
