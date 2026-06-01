let season_data_saved = {}

const fetchComps = function () {
    if (dataset) {
        fetch(`https://www.wheeloratings.com/src/afl_stats/${dataset}/comps.json`)
            .then((res) => res.json())
            .then((data) => {
                comps = data;

                if (!(comp && Object.keys(comps).includes(comp)))
                    comp = "afl"

                updateCompSeasons();
                updateComps();
            });
    }
}

const updateCompSeasons = function () {
    if (comp) {
        if (!(season && comps[comp].Seasons.includes(season)))
            season = comps[comp].CurrentSeason[0];

        history.replaceState(null, '', `?comp=${comp}&season=${season}`);
        updateTitle();
        fetchCompSeasonData();
        if (comp_changed) updateSeasons();
    }
}

// const fetchCompSeasons = function () {
//     if (dataset && comp) {
//         fetch(`https://www.wheeloratings.com/src/afl_stats/${dataset}/${comp}/meta.json`)
//             .then((res) => res.json())
//             .then((data) => {
//                 comp_meta = data;

//                 if (!(season && comp_meta.Seasons.includes(season)))
//                     season = comp_meta.CurrentSeason[0];

//                 fetchCompSeasonData();
//                 history.replaceState(null, '', `?comp=${comp}&season=${season}`);
//                 if (comp_changed) updateSeasons();
//             });
//     }
// }

const updateMissingColumns = function () {
    missing_columns = [];

    if (season_data) {
        if (typeof reactable_columns !== "undefined")
            reactable_columns.forEach((element) => {
                if (!Object.keys(season_data).includes(element)) {
                    missing_columns.push(element);
                }
            })
    }
}

const fetchCompSeasonData = function () {
    tableLoading(true);

    let selectedPlayers = [];
    if (typeof selectedRows !== "undefined" && typeof season_data !== "undefined" && season_data.PlayerId)
        selectedPlayers = selectedRows.map(x => season_data.PlayerId[x]);

    if (dataset && comp && season) {
        fetch(`https://www.wheeloratings.com/src/afl_stats/${dataset}/${comp}/${season}.json`)
            .then((res) => res.json())
            .then((data) => {
                if (Object.keys(data).includes("Data"))
                    season_data = data.Data;
                else
                    season_data = data;
                if (Object.keys(data).includes("Metadata"))
                    season_metadata = data.Metadata;

                if (!season_data_saved[comp]) season_data_saved[comp] = {}
                season_data_saved[comp][season] = season_data

                season_url = isNaN(season) ? "" : `&season=${season}`;
                updateMissingColumns();

                selectedRows = [];
                if (typeof selectedRows !== "undefined" && typeof season_data !== "undefined" && season_data.PlayerId)
                    selectedPlayers.forEach(x => {
                        if (season_data.PlayerId.indexOf(x) > 0) selectedRows.push(season_data.PlayerId.indexOf(x));
                    });
                updateOther();

                let seasonMetaText = "";
                if (typeof seasonMeta !== "undefined") {
                    if (season_metadata && season_metadata["Notes"])
                        seasonMetaText = `<p>${season_metadata["Notes"][0]}</p>`;

                    if (season_metadata && season_metadata["LatestGames"])
                        seasonMetaText = `${seasonMetaText}<p><b>Latest game(s):</b> ${season_metadata["LatestGames"][0]}</p>`;

                    if (seasonMetaText) {
                        seasonMeta.innerHTML = seasonMetaText
                        seasonMeta.classList.remove("d-none");
                    } else {
                        seasonMeta.innerHTML = "";
                        seasonMeta.classList.add("d-none");
                    }
                }

                Reactable.setData(reactableId, season_data);
                prepareChart();
                //updateHighlightTeams();
                tableLoading(false);
            });
    }
}

const updateTitle = function () {
    if (comps && comps[comp] && season) {
        season_label = comps[comp].SeasonLabels[comps[comp].Seasons.indexOf(season)];
        document.title = `${comps[comp].Abbreviation} ${page_title} - ${season_label}`;
        document.querySelector('meta[name="description"]').setAttribute('content', `${comps[comp].Abbreviation} ${page_title}.toLowerCase() for ${season_label}.`);
        document.querySelector('h1').innerText = `${comps[comp].Abbreviation} ${page_title} - ${season_label}`;
    }
}

const tableLoading = function (loading = true) {
    if (loading) {
        loadingIcon.classList.remove("d-none");
        statsTable.classList.add("d-none");
    } else {
        loadingIcon.classList.add("d-none");
        statsTable.classList.remove("d-none");
    }
}

const compButtons = [];
const seasonButtons = [];

const updateComps = function () {
    compSelect.innerHTML = "" //"<b>Competition:</b>";
    if (comps) {
        //for (element of [...Object.keys(comps)]) {
        Object.keys(comps).forEach((element) => {
            button = document.createElement('button');
            button.id = `comp-${element}`;
            button.type = "button";
            button.innerText = comps[element].Abbreviation;
            if (comp && comp == element)
                button.classList = "btn btm-sm mx-1 my-2 px-2 btn-primary";
            else
                button.classList = "btn btm-sm mx-1 my-2 px-2 btn-light";

            compSelect.appendChild(button);
            compButtons.push(button);

            button.addEventListener('click', (e) => {
                comp = element;
                // window.location.href = `${window.location.pathname}?comp=${element}`;
                // history.replaceState(null, '', `?comp=${comp}`);
                comp_changed = true;
                updateCompSeasons();

                for (btn of compButtons) {
                    if (btn.id === `comp-${element}`) {
                        btn.classList.add("btn-primary");
                        btn.classList.remove("btn-light");
                    } else {
                        btn.classList.add("btn-light");
                        btn.classList.remove("btn-primary");
                    }
                }
            })
        })
    }
}

const updateSeasons = function () {
    seasonSelect.innerHTML = "" //"<b>Season:</b>";
    if (comps && comps[comp]) {
        comps[comp].Seasons.forEach((element, index) => {
            button = document.createElement('button');
            button.id = `season-${element.replaceAll(".", "-")}`;
            button.type = "button";
            button.innerText = comps[comp].SeasonLabels[index];
            if (season && season == element)
                button.classList = "btn btm-sm mx-1 my-2 px-2 btn-primary";
            else
                button.classList = "btn btm-sm mx-1 my-2 px-2 btn-light";

            seasonSelect.appendChild(button);
            seasonButtons.push(button);

            button.addEventListener('click', (e) => {
                season = element;
                history.replaceState(null, '', `?comp=${comp}&season=${season}`);
                updateTitle();
                fetchCompSeasonData();

                for (btn of seasonButtons) {
                    if (btn.id === `season-${element.replaceAll(".", "-")}`) {
                        btn.classList.add("btn-primary");
                        btn.classList.remove("btn-light");
                    } else {
                        btn.classList.add("btn-light");
                        btn.classList.remove("btn-primary");
                    }
                }
            });
        });
    }

    comp_changed = false;
}

// const updateHighlightTeams = function () {
//     let highlightedTeam = highlightedTeamSelect.value;
//     let inSelection = false;

//     highlightedTeamSelect.innerHTML = "";

//     if (highlightValueOptions && highlightValueOptions.Team) {
//         const highlightTeams = ["None", ...highlightValueOptions.Team.sort()];

//         highlightTeams.forEach(element => {
//             const option = document.createElement("option");
//             option.value = element;
//             option.text = element;
//             highlightedTeamSelect.appendChild(option);

//             if (element === highlightedTeam) {
//                 highlightedTeamSelect.value = element;
//                 inSelection = true;
//             }
//         });
//     }

//     if (!inSelection) highlightedTeamSelect.value = "Average";
//     if (highlightedTeamSelect.selectedIndex === -1) highlightedTeamSelect.value = "None";
// }