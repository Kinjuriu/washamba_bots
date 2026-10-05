import csv, json, glob

def load_leaderboard(csv_path):
    lookup = {}
    with open(csv_path, encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        for row in r:
            lookup[int(row['TeamId'])] = dict(
                rank=int(row['Rank']), name=row['TeamName'],
                score=float(row['Score']), submissions=int(row['SubmissionCount']),
                last_sub=row['LastSubmissionDate'],
            )
    return lookup

def band(score):
    if score is None:
        return 'unknown'
    if score < 2000:
        return '<2000'
    if score < 2500:
        return '2000-2500'
    if score < 2800:
        return '2500-2800'
    return '>2800'
