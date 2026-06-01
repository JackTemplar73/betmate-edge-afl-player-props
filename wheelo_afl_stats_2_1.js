function storageAvailable(type) {
    let storage;
    try {
        storage = window[type];
        const x = '__storage_test__';
        storage.setItem(x, x);
        storage.removeItem(x);
        return true;
    }
    catch (e) {
        return e instanceof DOMException && (
            // everything except Firefox
            e.code === 22 ||
            // Firefox
            e.code === 1014 ||
            // test name field too, because code might not be present
            // everything except Firefox
            e.name === 'QuotaExceededError' ||
            // Firefox
            e.name === 'NS_ERROR_DOM_QUOTA_REACHED') &&
            // acknowledge QuotaExceededError only if there's something already stored
            (storage && storage.length !== 0);
    }
}

let playerStatSelections;
let showColumns = [];

if (storageAvailable('localStorage')) {
    playerStatSelections = JSON.parse(localStorage.getItem("playerStatSelections"));
}

const statsColumnsAll = ["RatingPoints_Avg", "Supercoach_Avg",
    "DreamTeamPoints_Avg", "CoachesVotes_Total", "CoachesVotes_Avg", "CoachesVotes_MatchesPolled", "BnFVotes_Total", "TimeOnGround", "Kicks", "Handballs", "Disposals",
    "DisposalEfficiency", "KickingEfficiency", "HandballEfficiency", "DisposalRetentionPercentage", "KicksIntoF50", "KickIntoF50RetentionPercentage", "KickPercentage", "Inside50s", "Rebound50s",
    "Clangers", "DisposalsPerClanger", "Turnovers", "DisposalsPerTurnover",
    "MetresGained", "MetresGainedPerDisposal", "AssistedMetresGained", "NetMetresGained", "KickMetresGained", "RetainedMetresGained", "KickMetresGainedPerKick", "HandballMetresGained", "HandballMetresGainedPerHandball",
    "Equity_PreClearance", "Equity_PostClearance", "Equity_Possession", "Equity_BallUse", "xThreatPerKick", "ThreatRating", "xRetainPerKick", "RetentionRating",
    "ContestedPossessions", "UncontestedPossessions", "TotalPossessions", "ContestedPossessionRate", "Intercepts",
    "GroundBallGets", "GroundBallGetsForward50", "GroundBallGetsDefensive50", "HardBallGets", "LooseBallGets", "PostClearanceContestedPossessions", "PostClearanceGroundBallGets", "GathersFromHitout", "CrumbingPossessions", "HandballReceives",
    "AverageFieldPosition", "Defensive50Possessions", "DefensiveMidfieldPossessions", "AttackingMidfieldPossessions", "Forward50Possessions",
    "CentreBounceAttendances", "CentreBounceAttendancePercentage", "CentreClearances", "CentreClearanceRate",
    "StoppageClearances", "TotalClearances", "FirstPossessions", "FirstPossessionToClearance", "Marks", "ContestedMarks", "MarksInside50", "InterceptMarks", "MarksOnLead",
    "FreesFor", "FreesAgainst", "FreesDiff", "RuckContests", "RuckContestPercentage", "Hitouts", "HitoutsWinPercentage",
    "HitoutsToAdvantage", "HitoutsToAdvantagePercentage", "RuckHardBallGets", "HitoutToFirstPossession", "HitoutToClearance", "Tackles", "TacklesInside50", "ContestDefensiveOneOnOnes",
    "ContestDefensiveLossPercentage", "ContestOffensiveOneOnOnes", "ContestOffensiveWinPercentage",
    "Goals_Total", "Goals_Avg", "Behinds", "ShotsAtGoal", "GoalAssists", "ScoreAssists", "ScoreboardImpact", "GoalAccuracy", "ScoreInvolvements",
    "ScoreInvolvementPercentage", "ScoreLaunches",
    "xScoreShots", "xScorePerShot", "xScoreRatingPerShot", "xScoreShots_Set", "xScorePerShot_Set", "xScoreRatingPerShot_Set",
    "xScoreShots_General", "xScorePerShot_General", "xScoreRatingPerShot_General",
    "KickIns", "KickInPercentage", "KickInsPlayOnPercentage",
    "Bounces", "OnePercenters", "PressureActs", "PressureActsDefensiveHalf", "Spoils"];

const columnsAlwaysHidden = ["PlayerId", "IsAFLListedPlayer", "Age_Decimal", "Team", "Image"];

let statsColumnsAvailable;

const statsColumns = {
    "Key stats": {
        "RatingPoints_Avg": null, "TimeOnGround": null, "Disposals": null, "MetresGained": null, "ContestedPossessions": null, "TotalPossessions": null,
        "CentreClearances": null, "TotalClearances": null, "Marks": null, "ContestedMarks": null, "Goals_Total": null, "Goals_Avg": null, "Tackles": null, "PressureActs": null, "Hitouts": null
    },
    "General": { "RatingPoints_Avg": "Player Rating", "Supercoach_Avg": "Supercoach Points", "DreamTeamPoints_Avg": "Fantasy Points", "CoachesVotes_Total": "Coaches Votes (Total)", "CoachesVotes_Avg": "Coaches Votes (Average)", "CoachesVotes_MatchesPolled": "Coaches Votes (Matches Polled)", "BnFVotes_Total": "B&F Votes", "TimeOnGround": "Time On Ground" },
    "Disposals": {
        "Kicks": "Kicks", "Handballs": "Handballs", "Disposals": "Disposals", "KickPercentage": "Kick %",
        "Inside50s": "Inside 50s", "Rebound50s": "Rebound 50s", "MetresGained": "Metres Gained", "MetresGainedPerDisposal": "Metres Gained Per Disposal",
        "AssistedMetresGained": "Assisted Metres Gained", "NetMetresGained": "Net Metres Gained", "RetainedMetresGained": "Retained Metres Gained", "KickMetresGained": "Kick Metres Gained", "KickMetresGainedPerKick": "Kick Metres Gained / Kick",
        "HandballMetresGained": "Handball Metres Gained", "HandballMetresGainedPerHandball": "Handball Metres Gained / Handball"
    },
    "Disposal Efficiency": {
        "KickingEfficiency": "Kicking Efficiency", "HandballEfficiency": "Handball Efficiency", "DisposalEfficiency": "Disposal Efficiency",
        "Clangers": "Clangers", "DisposalsPerClanger": "Disposals Per Clanger", "Turnovers": "Turnovers", "DisposalsPerTurnover": "Disposals Per Turnover",
        "DisposalRetentionPercentage": "Disposal Retention %", "KickIntoF50RetentionPercentage": "Kick Into F50 Retention %",
        "xThreatPerKick": "xThreat / Kick", "ThreatRating": "Threat Rating", "xRetainPerKick": "xRetain / Kick", "RetentionRating": "Retention Rating"
    },
    "Equity": { "Equity_PreClearance": "Pre-Clearance", "Equity_PostClearance": "Post-Clearance", "Equity_Possession": "Ball Winning", "Equity_BallUse": "Ball Use" },
    "Possessions": {
        "ContestedPossessions": "Contested Possessions", "UncontestedPossessions": "Uncontested Possessions", "TotalPossessions": "Total Possessions",
        "ContestedPossessionRate": "Contested Possession %", "Intercepts": "Intercept Possessions", "GroundBallGets": "Ground Ball Gets", "GroundBallGetsForward50": "Forward 50 Ground Ball Gets", "GroundBallGetsDefensive50": "Defensive 50 Ground Ball Gets",
        "HardBallGets": "Hard Ball Gets", "LooseBallGets": "Loose Ball Gets", "PostClearanceContestedPossessions": "Post-Clearance Contested Possessions", "PostClearanceGroundBallGets": "Post-Clearance Ground Ball Gets",
        "GathersFromHitout": "Gathers from Hitout", "CrumbingPossessions": "Crumbing Possessions", "HandballReceives": "Handball Receives",
        "AverageFieldPosition": "Possession Location Chart", "Defensive50Possessions": "Defensive 50 Possessions", "DefensiveMidfieldPossessions": "Defensive Midfield Possessions", "AttackingMidfieldPossessions": "Attacking Midfield Possessions", "Forward50Possessions": "Forward 50 Possessions"
    },
    "Clearances": {
        "CentreBounceAttendances": "Centre Bounce Attendances", "CentreBounceAttendancePercentage": "Centre Bounce Attendance %", "CentreClearances": "Centre Clearances", "CentreClearanceRate": "Centre Clearances Per CBA", "StoppageClearances": "Stoppage Clearances", "TotalClearances": "Total Clearances",
        "FirstPossessions": "First Possessions", "FirstPossessionToClearance": "First Possession To Clearance %"
    },
    "Marks": { "Marks": "Marks", "ContestedMarks": "Contested Marks", "MarksInside50": "Marks Inside Forward 50", "InterceptMarks": "Intercept Marks", "MarksOnLead": "Marks On Lead" },
    "Scoring/Attack": {
        "Goals_Total": "Goals (Total)", "Goals_Avg": "Goals (Average)", "Behinds": "Behinds", "ShotsAtGoal": "Shots At Goal", "GoalAssists": "Goal Assists",
        "ScoreAssists": "Score Assists", "ScoreboardImpact": "Scoreboard Impact",
        "GoalAccuracy": "Goal Accuracy", "ScoreInvolvements": "Score Involvements", "ScoreInvolvementPercentage": "Score Involvement %", "ScoreLaunches": "Score Launches",
        "ContestOffensiveOneOnOnes": "Offensive One-On-One Contests", "ContestOffensiveWinPercentage": "Offensive One-On-One Contest Win %"
    },
    "Expected Scores": {
        "xScoreShots": "Total Shots", "xScorePerShot": "xScore / Shot", "xScoreRatingPerShot": "Rating / Shot",
        "xScoreShots_Set": "Total Set Shots", "xScorePerShot_Set": "xScore / Shot (Set Shots)", "xScoreRatingPerShot_Set": "Rating / Shot (Set Shots)",
        "xScoreShots_General": "Total General Play Shots", "xScorePerShot_General": "xScore / Shot (General Play)", "xScoreRatingPerShot_General": "Rating / Shot (General Play)"
    },
    "Defence": { "ContestDefensiveOneOnOnes": "Defensive One-On-One Contests", "ContestDefensiveLossPercentage": "Defensive One-On-One Contest Loss %", "Tackles": "Tackles", "TacklesInside50": "Tackles Inside Forward 50", "PressureActs": "Pressure Acts", "PressureActsDefensiveHalf": "Defensive Half Pressure Acts", "Spoils": "Spoils" },
    "Ruck Contests": {
        "RuckContests": "Ruck Contests", "RuckContestPercentage": "Ruck Contest %", "Hitouts": "Hitouts", "HitoutsWinPercentage": "Hitout Win %", "HitoutsToAdvantage": "Hitouts To Advantage", "HitoutsToAdvantagePercentage": "Hitouts To Advantage %",
        "RuckHardBallGets": "Ruck Hard Ball Gets", "HitoutToFirstPossession": "Hitout To First Possession %", "HitoutToClearance": "Hitout To Clearance %"
    },
    "Other": { "FreesFor": "Frees For", "FreesAgainst": "Frees Against", "FreesDiff": "Frees Differential", "KickIns": "Kick-Ins", "KickInPercentage": "Kick-In %", "KickInsPlayOnPercentage": "Kick-In Play On %", "Bounces": "Bounces", "OnePercenters": "One Percenters" }
};

const match_count_column = 'Matches';

const filterColumns = {
    'Age': 'Age (at 31 December)',
    'Matches': 'Games',
    'TimeOnGround': 'Time On Ground %',
    'RatingPoints_Avg': 'Player Rating',
    'Supercoach_Avg': 'Supercoach',
    'Kicks_Avg': {
        column: 'Kicks',
        label: 'Kicks (Average)',
        total: false
    },
    'Kicks_Total': {
        column: 'Kicks',
        label: 'Kicks (Total)',
        total: true
    },
    'Handballs': 'Handballs',
    'Disposals_Avg': {
        column: 'Disposals',
        label: 'Disposals (Average)',
        total: false
    },
    'Disposals_Total': {
        column: 'Disposals',
        label: 'Disposals (Total)',
        total: true
    },
    'KicksIntoF50_Total': {
        column: 'KicksIntoF50',
        label: 'Kicks Into Forward 50 (Total)',
        total: true
    },
    'ContestedPossessions': 'Contested Possessions',
    'CentreBounceAttendancePercentage': 'Centre Bounce Attendance %',
    'CentreClearances': 'Centre Clearances',
    'TotalClearances': 'Clearances',
    'MetresGained': 'Metres Gained',
    'FirstPossessions': 'First Possessions',
    'Marks': 'Marks',
    'ContestedMarks': 'Contested Marks',
    'Goals_Total': 'Goals (Total)',
    'Goals_Avg': 'Goals (Average)',
    'GoalAssists': 'Goal Assists',
    'ContestOffensiveOneOnOnes_Avg': {
        column: 'ContestOffensiveOneOnOnes',
        label: 'Offensive One-On-One Contests (Average)',
        total: false
    },
    'ContestOffensiveOneOnOnes_Total': {
        column: 'ContestOffensiveOneOnOnes',
        label: 'Offensive One-On-One Contests (Total)',
        total: true
    },
    'ShotsAtGoal': 'Shots at Goal (Average)',
    'xScoreShots': 'Shots at Goal (Total)',
    'xScoreShots_Set': 'Set Shots (Total)',
    'xScoreShots_General': 'General Play Shots (Total)',
    'ContestDefensiveOneOnOnes_Avg': {
        column: 'ContestDefensiveOneOnOnes',
        label: 'Defensive One-On-One Contests (Average)',
        total: false
    },
    'ContestDefensiveOneOnOnes_Total': {
        column: 'ContestDefensiveOneOnOnes',
        label: 'Defensive One-On-One Contests (Total)',
        total: true
    },
    'Tackles': 'Tackles',
    'KickIns': 'Kick-Ins',
    'RuckContests': 'Ruck Contests',
    'HitoutsAvg': {
        column: 'Hitouts',
        label: 'Hitouts (Average)',
        total: false
    },
    'Hitouts_Total': {
        column: 'Hitouts',
        label: 'Hitouts (Total)',
        total: true
    }
}

const filterColumnsDefault = ['Age', 'Matches']

/* <h4>Select statistical categories to include in the table</h4>
<div id="stat-select">
// <select id="stat-select-presets" class="form-select" aria-label="Select stats for include in table">
// </select>
</div>
<div id="stat-select-custom" class="d-flex flex-wrap d-none">
</div> */

// const filtersDiv = document.querySelector("#filters");

// const statSelectAccordian = document.createElement('div');
// statSelectAccordian.classList = "accordion-item";

// const statSelectAccordianCollapse = document.createElement('div');
// statSelectAccordianCollapse.id = "collapse-stat-categories";
// statSelectAccordianCollapse.classList = "accordion-collapse collapse show";

// let statSelectDiv = document.querySelector("#stat-select-div");
// statSelectDiv.remove();

// statSelectDiv = document.createElement('div');
// statSelectDiv.id = "stat-select-div";
// statSelectDiv.classList = "accordion-body px-3 py-2";
// // statSelectDiv.ariaLabelledby = "stat-categories-select";
// statSelectDiv.dataset.bsParent = "#filters";

// // const h4 = document.createElement("h4");
// // h4.innerText = "Select statistical categories to include in the table";

// const h2 = document.createElement("h2");
// h2.id = "stat-categories-select";
// h2.classList = "accordion-header mt-0";

// const statCategoryButton = document.createElement('button');
// statCategoryButton.classList = "accordion-button";
// statCategoryButton.type = "button";
// statCategoryButton.dataset.bsToggle = "collapse";
// statCategoryButton.dataset.bsTarget = "#collapse-stat-categories";
// statCategoryButton.ariaExpanded = false;
// statCategoryButton.ariaControls = "collapse-stat-categories";
// statCategoryButton.innerText = "Select statistical categories";
// h2.appendChild(statCategoryButton);

const statSelectDiv = document.querySelector('#stat-select-div');
// const playerStatsDiv = document.querySelector('#player-stats-div');
const filtersDiv = document.querySelector("#filters");
const filtersIndicator = document.querySelector("#filters-indicator");

const csvDownloadButton = document.createElement('button');
csvDownloadButton.id = "download-csv-button";
csvDownloadButton.classList = "btn btn-primary btn-sm mx-1 my-2";
csvDownloadButton.innerText = "Download as CSV";
csvDownloadButton.addEventListener('click', (e) => {
    //Reactable.downloadDataCSV('player-stats-table', `afl-player-stats-${year}.csv`, { columnIds: [...['Player', 'Team', 'Age', 'Age_Decimal', 'Position', 'Matches'], ...statsColumnsAll.filter((value) => { return !["PlayerId", "WebsiteId", "Team", "Image", "IsAFLListedPlayer"].includes(value) })] });
    Reactable.downloadDataCSV('player-stats-table', `${comp}-player-stats-${season}.csv`, { columnIds: [...['Player', 'Team', 'Age', 'Age_Decimal', 'Position', 'Matches'], ...statsColumnsAll] });
    gtag('event', 'data_download');
});
// playerStatsDiv.appendChild(csvDownloadButton);
filtersDiv.insertAdjacentElement('afterend', csvDownloadButton);

const csvDownloadVisibleButton = document.createElement('button');
csvDownloadVisibleButton.id = "download-visible-csv-button";
csvDownloadVisibleButton.classList = "btn btn-primary btn-sm mx-1 my-2";
csvDownloadVisibleButton.innerText = "Download Visible Columns Only";
csvDownloadVisibleButton.addEventListener('click', (e) => {
    //Reactable.downloadDataCSV('player-stats-table', `afl-player-stats-${year}.csv`, { columnIds: [...['Player', 'Team', 'Age', 'Age_Decimal', 'Position', 'Matches'], ...statsColumnsAll.filter((value) => { return !["PlayerId", "WebsiteId", "Team", "Image", "IsAFLListedPlayer"].includes(value) })] });
    Reactable.downloadDataCSV('player-stats-table', `${comp}-player-stats-${season}.csv`, { columnIds: [...['Player', 'Team', 'Age', 'Age_Decimal', 'Position', 'Matches'], ...showColumns] });
    gtag('event', 'data_download');
});
// playerStatsDiv.appendChild(csvDownloadButton);
csvDownloadButton.insertAdjacentElement('afterend', csvDownloadVisibleButton);

const statCategoryAccordian = document.querySelector('#accordion-stat-categories');
statCategoryAccordian.classList.remove('d-none');

const statCategoryCollapse = document.querySelector('#collapse-stat-categories');
const statCategoryButton = document.querySelector('#collapse-stat-categories-button');

const playerFilterSelect = document.querySelector('#player-select');
const teamFilterSelect = document.querySelector('#team-select');
const positionFilterSelect = document.querySelector('#position-select');

if (playerStatSelections && playerStatSelections.length > 0) {
    statCategoryCollapse.classList.remove("show");
    statCategoryButton.classList.add("collapsed");
    statCategoryButton.ariaExpanded = "false";
} else {
    // const newAlert = document.createElement("span");
    // newAlert.classList = "badge bg-primary mx-2";
    // newAlert.innerText = "New";
    // statCategoryButton.appendChild(newAlert);
}

const statSelect = document.createElement("div");
statSelect.id = "stat-select";
const customStatDiv = document.createElement("div");
customStatDiv.id = "stat-select-custom";
customStatDiv.classList = "d-flex flex-wrap";

const customStatDivParent = document.createElement("div");
customStatDivParent.classList = "d-none";

// statSelectDiv.appendChild(h4);
// statSelectAccordian.appendChild(h2);
// statSelectAccordianCollapse.appendChild(statSelectDiv);
// statSelectAccordian.appendChild(statSelectAccordianCollapse);
// filtersDiv.appendChild(statSelectAccordian);

const paraCustomWarning = document.createElement('p');
paraCustomWarning.classList = "small my-1 d-none";
paraCustomWarning.innerHTML = "<b>Custom</b> needs to be selected and <b>Show all</b> needs to be de-selected for custom selections to be reflected."

const paraMissingFieldWarning = document.createElement('p');
paraMissingFieldWarning.classList = "small my-1 text-danger";
paraMissingFieldWarning.innerHTML = "Fields in red are not available for the selected competition and season."

const customSelectAllButton = document.createElement('button');
customSelectAllButton.classList = "btn btn-primary btn-sm mx-1 my-2";
customSelectAllButton.innerText = "Select All";
customSelectAllButton.addEventListener('click', () => {
    document.querySelectorAll("#stat-select-custom input:not(:checked)").forEach((element) => element.checked = true);
    updateTableColumns(id = null, custom = true)
});

const customSelectNoneButton = document.createElement('button');
customSelectNoneButton.classList = "btn btn-primary btn-sm mx-1 my-2";
customSelectNoneButton.innerText = "Clear All";
customSelectNoneButton.addEventListener('click', () => {
    document.querySelectorAll("#stat-select-custom input:checked").forEach((element) => element.checked = false);
    updateTableColumns(id = null, custom = true)
});

statSelectDiv.appendChild(statSelect);
statSelectDiv.appendChild(customStatDivParent);
customStatDivParent.appendChild(paraCustomWarning);
customStatDivParent.appendChild(paraMissingFieldWarning);
customStatDivParent.appendChild(customSelectAllButton);
customStatDivParent.appendChild(customSelectNoneButton);
customStatDivParent.appendChild(customStatDiv);

const updateTableColumns = function (id = null, custom = false) {
    showColumns = [];
    const customSelections = document.querySelectorAll("#stat-select-custom input:checked").length;

    if (custom) { customTextSpan.innerText = `(${customSelections} selected)` };

    if (selectShowAll.checked) {
        //Reactable.setHiddenColumns('player-stats-table', ["PlayerId", "Age_Decimal", "Team", "Image", "IsAFLListedPlayer", ...missing_columns]);
        Reactable.setHiddenColumns('player-stats-table', [...columnsAlwaysHidden, ...missing_columns]);
    } else if (selectCustom.checked) {
        const selectedInputs = document.querySelectorAll("#stat-select-custom input:checked");

        for (input of selectedInputs) {
            showColumns = [...showColumns, input.value];
        }

        Reactable.setHiddenColumns('player-stats-table', [...statsColumnsAll.filter((el) => !showColumns.includes(el)), ...columnsAlwaysHidden, ...missing_columns]);
    } else if (!custom) {
        const selectedInputs = document.querySelectorAll("#stat-select input:checked");

        for (input of selectedInputs) {
            showColumns = [...showColumns, ...Object.keys(statsColumns[input.value])];
        }

        Reactable.setHiddenColumns('player-stats-table', [...statsColumnsAll.filter((el) => !showColumns.includes(el)), ...columnsAlwaysHidden, ...missing_columns]);
    }

    if (selectShowAll.checked || !selectCustom.checked) {
        paraCustomWarning.classList.remove("d-none");
    } else {
        paraCustomWarning.classList.add("d-none")
    };

    if (!custom) {
        const inputs = document.querySelectorAll("#stat-select input");

        for (input of inputs) {
            if (input === selectCustom) {
                input.disabled = selectShowAll.checked;
            } else if (input !== selectShowAll) {
                input.disabled = (selectShowAll.checked || selectCustom.checked);
            }
        }
    }

    if (id === "select-custom" && selectCustom.checked) {
        toggleCustomStatDivDisplay(true);
    } else if (id === "select-custom" && !selectCustom.checked) {
        toggleCustomStatDivDisplay(false);
    }
};

const setFilter = function (columnId, value) {
    Reactable.setFilter(reactableId, columnId, value);
    updateFiltersIndicator();
}

const filterPlayer = function () {
    if ($('#player-select')[0].selectize.items.length == 0) {
        setFilter("PlayerId", undefined);
    } else {
        setFilter("PlayerId", $('#player-select')[0].selectize.items);
    }
};

const filterTeam = function () {
    if ($('#team-select')[0].selectize.items.length == 0) {
        setFilter("Team", undefined);
    } else {
        setFilter("Team", $('#team-select')[0].selectize.items);
    }
};

const filterPosition = function () {
    if ($('#position-select')[0].selectize.items.length == 0) {
        setFilter("Position", undefined);
    } else {
        setFilter("Position", $('#position-select')[0].selectize.items);
    }
};

$('#player-select').selectize({
    maxItems: null,
    valueField: 'id',
    labelField: 'title',
    searchField: 'title',
    options: [],
    onChange: filterPlayer,
    create: false
});

$('#team-select').selectize({
    maxItems: null,
    valueField: 'title',
    labelField: 'title',
    searchField: 'title',
    options: [],
    onChange: filterTeam,
    create: false
});

$('#position-select').selectize({
    maxItems: null,
    valueField: 'title',
    labelField: 'title',
    searchField: 'title',
    options: [],
    onChange: filterPosition,
    create: false
});

const setPlayerFilterOptions = function () {
    const playerFilterOptions = [];
    const selectedPlayers = $('#player-select')[0].selectize.items;
    $('#player-select')[0].selectize.clearOptions();

    if (typeof season_data !== "undefined" && season_data["PlayerId"]) {
        season_data["PlayerId"].forEach((value, index) => {
            playerFilterOptions.push({ id: value, title: `${season_data["Player"][index]} (${season_data["Abbreviation"][index]})` })
        });

        playerFilterOptions.sort((a, b) => a.title.localeCompare(b.title));

        $('#player-select')[0].selectize.addOption(playerFilterOptions);
        $('#player-select')[0].selectize.addItems(selectedPlayers);
    }
}

const setUniqueFilterOptions = function (columnId, selectId) {
    const filterOptions = [];
    const selectedPositions = $(selectId)[0].selectize.items;
    $(selectId)[0].selectize.clearOptions();

    // if (highlightValueOptions && highlightValueOptions[columnId] && highlightValueOptions[columnId].length > 0 && highlightValueOptions[columnId][0]) {
    //     highlightValueOptions[columnId].sort().forEach((value, index) => {
    //         filterOptions.push({ title: value })
    //     });
    // }
    if (typeof season_data !== "undefined" && season_data[columnId]) {
        const uniquePositions = new Set(season_data[columnId]);
        [...uniquePositions].sort().forEach((value) => {
            filterOptions.push({ title: value })
        })
    }

    $(selectId)[0].selectize.addOption(filterOptions);
    if (!missing_columns.includes(columnId))
        $(selectId)[0].selectize.addItems(selectedPositions);

    if (filterOptions.length == 0)
        document.querySelector(selectId).parentElement.classList.add("d-none");
    else
        document.querySelector(selectId).parentElement.classList.remove("d-none");
}

const setPositionFilterOptions = function () {
    const positionFilterOptions = [];
    const selectedPositions = $('#position-select')[0].selectize.items;
    $('#position-select')[0].selectize.clearOptions();

    if (highlightValueOptions && highlightValueOptions.Position && highlightValueOptions.Position.length > 0 && highlightValueOptions.Position[0]) {
        highlightValueOptions.Position.sort().forEach((value, index) => {
            positionFilterOptions.push({ title: value })
        });
    } else if (typeof season_data !== "undefined" && season_data["Position"]) {
        const uniquePositions = new Set(season_data["Position"]);
        [...uniquePositions].sort().forEach((value) => {
            positionFilterOptions.push({ title: value })
        })
    }

    $('#position-select')[0].selectize.addOption(positionFilterOptions);
    if (!missing_columns.includes("Position"))
        $('#position-select')[0].selectize.addItems(selectedPositions);

}

const updateOther = function () {
    if (comps && comps[comp] && comps[comp].IsMatchStats && comps[comp].IsMatchStats[0] == "Yes") {
        if (missing_columns.indexOf("WebsiteId") >= 0) missing_columns.splice(missing_columns.indexOf("WebsiteId"))
    } else {
        missing_columns = new Set([...missing_columns, "WebsiteId"])
        missing_columns = [...missing_columns]
    }

    updateTableColumns();

    setPlayerFilterOptions();
    setUniqueFilterOptions("Team", "#team-select");
    setUniqueFilterOptions("Position", "#position-select");

    try {
        if (selectedPlayersOnly)
            Reactable.setFilter(reactableId, "Select", selectedRows)
        else
            Reactable.setFilter(reactableId, "Select", undefined)
    } catch (e) { }

    document.querySelectorAll("#stat-select-custom label").forEach(element => {
        if (missing_columns.includes(element.dataset.column))
            element.classList.add("text-danger")
        else
            element.classList.remove("text-danger")
    })

    updateFiltersIndicator();
}

const updateFiltersIndicator = function () {
    if (Reactable.getState(reactableId).filters.length) {
        filtersIndicator.classList.remove("d-none");
    } else {
        filtersIndicator.classList.add("d-none");
    }

    let filterWarnings = false;

    document.querySelectorAll("[id^=filter-warning]").forEach((element) => {
        if (element && element.dataset.column && missing_columns.includes(element.dataset.column))
            element.classList.remove("d-none")
        else
            element.classList.add("d-none")
    })

    document.getElementById("filters-indicator-warning").classList.add("d-none");

    Reactable.getState(reactableId).filters.forEach((value) => {
        if (missing_columns.includes(value.id)) {
            filterWarnings = true;

            document.getElementById("filters-indicator-warning").classList.remove("d-none")
        }
    })
}

const saveButton = document.createElement('button');
const saveButtonInitialText = "Save selections";
saveButton.id = "save-button";
saveButton.classList = "btn btn-primary btn-sm mx-1 my-2";
saveButton.innerText = saveButtonInitialText;
saveButton.style.width = "130px";

const saveSelections = function () {
    const selections = [];

    const selectedInputs = [...document.querySelectorAll("#stat-select input:checked"), ...document.querySelectorAll("#stat-select-custom input:checked")];
    for (input of selectedInputs) {
        selections.push(input.id);
    }

    if (storageAvailable("localStorage")) {
        localStorage.setItem("playerStatSelections", JSON.stringify(selections));
        gtag('event', 'save_stat_selections');

        saveButton.innerText = "Saved!";
        setTimeout(() => {
            saveButton.innerText = saveButtonInitialText;
        }, 500);
    }
};

// const statDropdown = document.querySelector("#stat-select-presets");

const customTextSpan = document.createElement('span');
customTextSpan.classList = "ps-1 fw-bold";

for (c of [...Object.keys(statsColumns), 'Custom', 'Show all']) {
    // const option = new Option(c, c);
    // statDropdown.add(option);

    const div = document.createElement('div');
    div.classList = "form-check form-switch";

    const id = "select-" + c.toLowerCase().replace(/[\W_]+/g, '-');

    const input = document.createElement('input');
    input.classList = "form-check-input"
    input.type = "checkbox"
    input.value = c;
    input.id = id;

    if (playerStatSelections && playerStatSelections.includes(id)) {
        input.checked = true
    } else if (!playerStatSelections && c === Object.keys(statsColumns)[0]) {
        input.checked = true;
    }

    input.addEventListener('change', (e) => {
        updateTableColumns(id);
    });

    const label = document.createElement('label');
    label.classList = "form-check-label stat-selection-label"
    if (c === "Custom" || c === 'Show all') { label.classList += " fw-bold" }
    label.htmlFor = id;
    label.innerText = c;

    if (c === "Custom") {
        label.appendChild(customTextSpan)
    }

    div.appendChild(input)
    div.appendChild(label)

    statSelect.appendChild(div);
}

const selectShowAll = document.querySelector("#select-show-all");
const selectCustom = document.querySelector("#select-custom");

let customStatDivDisplayed = false;

const toggleCustomStatDivDisplay = function (show = null) {
    if (show === null) {
        customStatDivDisplayed = !customStatDivDisplayed;
    } else {
        customStatDivDisplayed = show;
    }

    if (customStatDivDisplayed) {
        customButton.innerText = "Hide custom fields";
        customStatDivParent.classList.remove("d-none")
    } else {
        customButton.innerText = "Show custom fields";
        customStatDivParent.classList.add("d-none")
    }
}

const customButton = document.createElement('button');
customButton.id = "custom-button";
customButton.classList = "btn btn-primary btn-sm mx-1 my-2";
customButton.style.width = "150px";

toggleCustomStatDivDisplay(false);

// customButton.addEventListener("click", () => customStatDiv.style.display === "none" ? customStatDiv.style.display = "" : customStatDiv.style.display = "none");
customButton.addEventListener("click", () => toggleCustomStatDivDisplay());

statSelect.appendChild(customButton)

if (storageAvailable("localStorage")) {
    saveButton.addEventListener("click", saveSelections);
    statSelect.appendChild(saveButton);
}

for (c of Object.keys(statsColumns).splice(1)) {
    const statCategoryDiv = document.createElement('div');
    statCategoryDiv.classList = "m-2";

    const h5 = document.createElement('h5');
    h5.classList = "my-1"
    h5.innerText = c;

    statCategoryDiv.appendChild(h5)

    for (s of Object.keys(statsColumns[c])) {
        const div = document.createElement('div');
        div.classList = "form-check form-switch";

        const id = "select-custom-" + s.toLowerCase().replaceAll(' ', '-');

        const input = document.createElement('input');
        input.classList = "form-check-input"
        input.type = "checkbox"
        input.value = s;
        input.id = id;

        if (playerStatSelections && playerStatSelections.includes(id)) {
            input.checked = true
        }

        input.addEventListener('change', (e) => { updateTableColumns(id, true); });

        const label = document.createElement('label');
        label.classList = "form-check-label stat-selection-label"
        label.dataset.column = s;
        label.htmlFor = id;
        label.innerText = statsColumns[c][s];

        div.appendChild(input);
        div.appendChild(label);
        statCategoryDiv.appendChild(div)
    }

    customStatDiv.appendChild(statCategoryDiv)
}

customTextSpan.innerText = `(${document.querySelectorAll("#stat-select-custom input:checked").length} selected)`;

// statDropdown.addEventListener('change', (e) => {
//   showColumns = statsColumns[statDropdown.value];
//   updateTableColumns();
// });

window.addEventListener('DOMContentLoaded', (event) => { updateTableColumns() });

const checkbox = document.querySelector("#showAFLListedPlayers");
if (checkbox) checkbox.checked = false;

checkbox.addEventListener('change', function () {
    if (checkbox.checked) {
        setFilter("IsAFLListedPlayer", [1])
    } else {
        setFilter("IsAFLListedPlayer", undefined)
    }
});