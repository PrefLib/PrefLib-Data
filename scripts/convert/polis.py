from __future__ import annotations

from preflibtools.instances import CategoricalInstance

import csv
import os
from collections.abc import Iterable


class PolisComment:
    """
    Represents a single comment in a Polis poll.

    Attributes:
        comment (str): The text of the comment.
        timestamp (str): The timestamp when the comment was created.
        comment_id (str): Unique identifier for the comment.
        author_id (str): Unique identifier of the comment's author.
        num_agrees (int): Number of participants who agreed with the comment.
        num_disagrees (int): Number of participants who disagreed with the comment.
        extra (dict): Optional dictionary for storing additional metadata.
    """

    def __init__(self, comment: str, timestamp: str, comment_id: str, author_id: str, num_agrees: int, num_disagrees: int, extra: dict = None):
        """
        Initialize a PolisComment instance.

        Args:
            comment (str): The comment text.
            timestamp (str): The time the comment was posted.
            comment_id (str): Unique ID for the comment.
            author_id (str): ID of the participant who wrote the comment.
            num_agrees (int): Number of agrees the comment received.
            num_disagrees (int): Number of disagrees the comment received.
            extra (dict, optional): Additional metadata (default: empty dict).
        """
        self.comment = comment
        self.timestamp = timestamp
        self.comment_id = comment_id
        self.author_id = author_id
        self.num_agrees = num_agrees
        self.num_disagrees = num_disagrees
        if extra is None:
            extra = dict()
        self.extra = extra

    def __str__(self):
        return f"Comment [{self.comment_id}]: {self.comment}"

class PolisParticipant:
    """
    Represents a participant in a Polis poll.

    Attributes:
        participant_id (str): Unique identifier of the participant.
        votes (dict[str, int | None]): Mapping of comment IDs to votes: 1 = agree, -1 = disagree, None = pass/skip.
    """

    def __init__(self, participant_id: str, votes: dict[str, int | None] = None):
        """
        Initialize a PolisParticipant instance.

        Args:
            participant_id (str): Unique ID for the participant.
            votes (dict[str, int | None], optional): Votes cast by the participant.
                Defaults to an empty dict.
        """
        self.participant_id = participant_id
        if votes is None:
            votes = dict()
        self.votes = votes

    def __str__(self):
        return f"Participant [{self.participant_id}]"

class PolisPoll:
    """
    Represents a full Polis poll with comments and participants.

    Attributes:
        name (str): Name of the poll.
        url (str): URL of the poll.
        comments (list[PolisComment]): List of comments in the poll.
        participants (list[PolisParticipant]): List of participants in the poll.
        description (str): Optional description of the poll.
    """

    def __init__(self, name: str = None, url: str = None, comments: Iterable[PolisComment] = None, participants: Iterable[PolisParticipant] = None, description: str = None):
        """
        Initialize a PolisPoll instance.

        Args:
            name (str, optional): The poll's name (default: empty string).
            url (str, optional): The poll's URL (default: empty string).
            comments (Iterable[PolisComment], optional): Comments in the poll.
                Defaults to an empty list.
            participants (Iterable[PolisParticipant], optional): Participants in the poll.
                Defaults to an empty list.
            description (str, optional): Description of the poll.
        """

        if name is None:
            name = ""
        self.name = name
        if url is None:
            url = ""
        self.url = url
        if comments is None:
            comments = []
        self.comments = list(comments)
        if participants is None:
            participants = []
        self.participants = list(participants)
        self.description = description

    @property
    def num_comments(self) -> int:
        """Return the number of comments in the poll."""
        return len(self.comments)

    @property
    def num_participants(self) -> int:
        """Return the number of participants in the poll."""
        return len(self.participants)

    def __str__(self):
        return f"Poll {self.name}"

def read_polis_summary(file_path: str) -> PolisPoll:
    """
    Read the `summary.csv` file and construct a `PolisPoll` object
    with basic metadata (topic, URL, description).

    Args:
        file_path (str): Path to the summary CSV file.

    Returns:
        PolisPoll: A poll with metadata fields populated, but without
        comments or participants yet.
    """
    poll = PolisPoll()
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue  # skip malformed rows
            key = row[0].strip()
            # join rest of row columns if any, since value can contain commas and newlines
            value = ','.join(row[1:]).strip()
            if key == "topic":
                poll.name = value
            elif key == "url":
                poll.url = value
            elif key == "conversation-description":
                poll.description = value
    return poll

def read_polis_comments(file_path: str) -> list[PolisComment]:
    """
    Read the `comments.csv` file and return a list of `PolisComment` objects.

    Args:
        file_path (str): Path to the comments CSV file.

    Returns:
        list[PolisComment]: A list of all comments in the poll.
    """
    all_comments = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract required fields
            comment = row.pop("comment-body")
            timestamp = row.pop("timestamp")
            comment_id = row.pop("comment-id")
            author_id = row.pop("author-id")
            num_agrees = int(row.pop("agrees"))
            num_disagrees = int(row.pop("disagrees"))

            # Any remaining columns are stored in "extra"
            extra = row
            all_comments.append(PolisComment(comment, timestamp, comment_id, author_id, num_agrees, num_disagrees, extra))
    return all_comments

def read_polis_participants(file_path: str, comment_ids: list[str]) -> list[PolisParticipant]:
    """
    Read the `participants-votes.csv` file and return a list of `PolisParticipant` objects.

    Args:
        file_path (str): Path to the participants CSV file.
        comment_ids (list[str]): List of comment IDs for which votes should be recorded.

    Returns:
        list[PolisParticipant]: A list of participants with their votes.
    """
    all_participants = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            participant_id = row.pop("participant")
            participant = PolisParticipant(participant_id)

            # Fill in votes for each known comment ID
            for comment_id in comment_ids:
                vote = row.get(comment_id)
                if vote:
                    participant.votes[comment_id] = int(vote)
                else:
                    participant.votes[comment_id] = None
            all_participants.append(participant)
    return all_participants

def read_polis_poll(dir_path: str) -> PolisPoll:
    """
    Read a full Polis poll from a directory containing:
      - `summary.csv`
      - `comments.csv`
      - `participants-votes.csv`

    Args:
        dir_path (str): Path to the directory with Polis poll CSV files.

    Returns:
        PolisPoll: A complete poll object with metadata, comments, and participants.
    """

    print("Reading polis poll raw_data from: " + dir_path)

    # Load poll summary (name, url, description)
    summary_path = os.path.join(dir_path, "summary.csv")
    poll = read_polis_summary(summary_path)

    # Load poll comments
    comments_path = os.path.join(dir_path, 'comments.csv')
    poll.comments = read_polis_comments(comments_path)

    # Load poll participants (requires comment IDs to map votes)
    participants_path = os.path.join(dir_path, 'participants-votes.csv')
    comment_ids = [str(c.comment_id) for c in poll.comments]
    poll.participants = read_polis_participants(participants_path, comment_ids)

    return poll

DESCRIPTION = {
    "15-per-hour-seattle": "New minimum wage in Seattle: $15/hour",
    "american-assembly.bowling-green": "Improving Bowling Green / Warren County",
    "austria-climate.2vkxcncppn.2022-07-07": "Wir, der Klimarat, wollen deine Meinungen und Ideen zum Thema ENERGIE hören, um eine klimafreundliche Zukunft zu erreichen.",
    "austria-climate.5twd2jsnkf.2022-08-08": "Wir, die Bürger:innen des Klimarats, wollen deine Meinungen und Ideen zum Thema PRODUKTION UND KONSUM hören, um Klimaneutralität bis 2040 zu erreichen.",
    "austria-climate.5tzfrp5eaa.2022-07-07": "Wir, die Bürger:innen des Klimarats, wollen deine Meinungen und Ideen zum Thema MOBILITÄT hören, um Klimaneutralität bis 2040 zu erreichen.",
    "austria-climate.7z7ejpbmv5.2022-08-08": "Wir, die Bürger:innen des Klimarats, wollen deine Meinungen und Ideen zum Thema WOHNEN hören, um Klimaneutralität bis 2040 zu erreichen.",
    "austria-climate.9xnndurbfm.2022-07-07": "Wir, die Bürger:innen des Klimarats, wollen deine Meinungen und Ideen zum Thema ERNÄHRUNG UND LANDNUTZUNG hören, um eine klimafreundliche Zukunft zu erreichen.",
    "bg2050-volunteers": "What would you want to see in the Bowling Green of the future?",
    "brexit-consensus": "Can there be consensus on Brexit?",
    "canadian-electoral-reform": "Canadian Electoral Reform",
    "football-concussions": "Concussions in the NFL",
    "london.youth.policing": "What is the best way to engage more young people in local scrutiny of policing?",
    "march-on.operation-marchin-orders": "Operation Marching Orders",
    "scoop-hivemind.affordable-housing": "Affordable Housing in New Zealand",
    "scoop-hivemind.biodiversity": "Protecting and Restoring New Zealand's Biodiversity",
    "scoop-hivemind.freshwater": "Freshwater Quality in New Zealand",
    "scoop-hivemind.taxes": "Fair enough? How should New Zealanders be taxed?",
    "scoop-hivemind.ubi": "A Universal Basic Income for Aotearoa NZ?",
    "ssis.land-bank-farmland.2rumnecbeh.2021-08-01": "Land use and conservation in the San Juan Islands",
    "vtaiwan.uberx": "UberX 自用車載客 — vTaiwan.tw",
}

def polis_poll_to_preflib_cat(poll_dir_path: str, preflib_file_name: str):
    polis_poll = read_polis_poll(poll_dir_path)

    instance = CategoricalInstance()
    instance.file_path = ""
    instance.file_name = preflib_file_name
    instance.modification_type = "original"
    if polis_poll.name:
        instance.title = f"Polis Poll: {polis_poll.name}"
    else:
        instance.title = "Polis Poll"
    instance.publication_date = "2025-06-15"
    instance.modification_date = "2025-06-15"
    instance.description = DESCRIPTION[os.path.basename(poll_dir_path)]

    instance.num_categories = 3
    instance.categories_name = {
        0: "Disapproved",
        1: "Neutral/Skipped",
        2: "Approved"
    }

    com_id_to_alts = {}

    for i, comment in enumerate(polis_poll.comments):
        instance.alternatives_name[i] = f"Comment #{comment.comment_id}"
        com_id_to_alts[comment.comment_id] = i

    instance.num_alternatives = len(instance.alternatives_name)

    for participant in polis_poll.participants:
        preferences = [[], [], []]
        for comment_id, vote in participant.votes.items():
            if vote == 0:
                preferences[1].append(com_id_to_alts[comment_id])
            elif vote == 1:
                preferences[2].append(com_id_to_alts[comment_id])
            elif vote == -1:
                preferences[0].append(com_id_to_alts[comment_id])
            elif vote is None:
                pass
            else:
                raise ValueError(f"Invalid vote: {vote}")
        hashable_pref = (tuple(preferences[0]), tuple(preferences[1]), tuple(preferences[2]))
        if hashable_pref in instance.multiplicity:
            instance.multiplicity[hashable_pref] += 1
        else:
            instance.multiplicity[hashable_pref] = 1
            instance.preferences.append(hashable_pref)

    instance.recompute_cardinality_param()

    return instance

if __name__ == "__main__":
    current_path = os.path.dirname(os.path.abspath(__file__))
    dataset_dir_path = os.path.join(current_path, "..", "..", "datasets", "00069 - polis")
    os.makedirs(dataset_dir_path, exist_ok=True)
    instances = []
    for i, poll in enumerate(os.listdir(os.path.join(current_path, "polis_data"))):
        file_name = f"00069-000000{str(i + 1) if i > 8 else f'0{i + 1}'}.cat"
        instance = polis_poll_to_preflib_cat(os.path.join(current_path, "polis_data", poll), file_name)
        instance.write(os.path.join(dataset_dir_path, file_name))
        instances.append(instance)

    with open(os.path.join(dataset_dir_path, "info.txt"), "w", encoding="utf-8") as info_file:
        info_file.write(f"""Name: "Pol.is

Abbreviation: polis

Tags: Election

Series Number: 00069

Publication Date: 2025-10-16

Description: <p><a href="https://pol.is/signin">Polis</a> is a survey software that allows users to share their opinions and ideas over statements and comments regarding a given theme.</p><p>The data presented here is a reformat of the Polis data available on <a href="https://github.com/compdemocracy/openData/tree/master">GitHub</a> under under a Creative Commons Attribution 4.0 International license. The data has been reformated to fit the PrefLib categorical preferences data.</p><p>Each file describes a polis poll. The alternatives correspond to the statements/comments from the polls. For each statement, the voters can either express positive opinion (corresponding to the "Approved" category), negative opinion (corresponding to the "disapproved" category), or the absence of opinion (in the "Neutral/Skipped" category). Voters do not have to express an opinion, or absence thereof, for all statements/comments.</p><p>The data has been provided by Simon Rey, as part of the development of the <a href="https://simon-rey.github.io/ProportionalityPress/">Proportionality Press</a> within the Fair online group decision making (FairOGD) project of <a href="https://janmaly.de/">Jan Maly</a>.</p>

Required Citations: 
        
Selected Studies:

file_name, modification_type, relates_to, title, description, publication_date\n""")
        for instance in instances:
            info_file.write(", ".join([str(i) if i is not None else '' for i in [instance.file_name, instance.modification_type, '', instance.title, instance.description, instance.publication_date]]) + "\n")
