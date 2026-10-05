"""Reusable helpers for episode fetching via the authenticated kagglesdk EpisodeService,
built for this session only (read-only research). Not part of the committed repo."""
import json, os, gzip, time
from kagglesdk import KaggleClient
from kagglesdk.competitions.types.competition_api_service import (
    ApiListSubmissionEpisodesRequest, ApiGetEpisodeReplayRequest, ApiGetEpisodeAgentLogsRequest,
    ApiListTeamPublicSubmissionsRequest,
)

def client():
    return KaggleClient()

def list_submission_episodes(c, submission_id):
    req = ApiListSubmissionEpisodesRequest(); req.submission_id = submission_id
    resp = c.competitions.competition_api_client.list_submission_episodes(req)
    out = []
    for e in resp.episodes:
        row = dict(episode_id=e.id, create_time=str(e.create_time), end_time=str(e.end_time),
                   state=str(e.state).split('.')[-1], type=str(e.type).split('.')[-1], agents=[])
        for a in e.agents:
            row['agents'].append(dict(submission_id=a.submission_id, index=a.index, reward=a.reward,
                                       team_name=a.team_name, team_id=a.team_id))
        out.append(row)
    return out

def list_team_public_submissions(c, team_id):
    req = ApiListTeamPublicSubmissionsRequest(); req.team_id = team_id
    resp = c.competitions.competition_api_client.list_team_public_submissions(req)
    return [dict(id=s.id, date_submitted=str(s.date_submitted), public_score=s.public_score) for s in resp.submissions]

def get_replay_bytes(c, episode_id):
    req = ApiGetEpisodeReplayRequest(); req.episode_id = episode_id
    resp = c.competitions.competition_api_client.get_episode_replay(req)
    resp.raise_for_status()
    return resp.content

def get_agent_logs_bytes(c, episode_id, agent_index):
    req = ApiGetEpisodeAgentLogsRequest(); req.episode_id = episode_id; req.agent_index = agent_index
    resp = c.competitions.competition_api_client.get_episode_agent_logs(req)
    resp.raise_for_status()
    return resp.content
