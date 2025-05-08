//////////////////
// Tagify Setup //
//////////////////
document.addEventListener('DOMContentLoaded', () => {
    var flagWhiteList = ["Software Name", "RP Name", "Software Description", "AI Description", 
    "Core Features", "Software Documentation", "Software Type", "Research Area", "Research Discipline", 
    "General Tags", "Software's Web Page", "Research Field", "Example Software Use", 
    "RP Software Documentation", "Version Info", "Software Class"];
    
    var software_whitelist = document.querySelector('#software_name_import');
    var rp_whitelist = document.querySelector('#rp_name_import');

    const includeForm = document.querySelector('input[name=include]');
    const include_tags_list = document.getElementById('include_tags_list');


    var rp_name = document.querySelector('input[name=rp_name]'),
        rpNameTagify = new Tagify(rp_name, {
            userInput: true,
            whitelist: rp_whitelist.value.split(", "),
            dropdown: {
                position: "manual",
                maxItems: Infinity,
                enabled: 1,
                classname: "customSuggestionsList"
            },
            templates: {
                dropdownItemNoMatch() {
                    return 'No match!';
                }
            },
            enforceWhitelist: true
    });


    var software_name = document.querySelector('input[name=software_name]'),
        softwareNameTagify = new Tagify(software_name, {
            userInput: true,
            whitelist: software_whitelist.value.split(", "),

            dropdown: {
                position: "manual",
                maxItems: Infinity,
                enabled: 1,
                classname: "customSuggestionsList"
            },
            templates: {
                dropdownItemNoMatch() {
                    return 'No match!';
                }
            },
            enforceWhitelist: true
    });

    var include = document.querySelector('input[name=include]'),
        includeTagify = new Tagify(include, {
            userInput: true,
            whitelist: flagWhiteList,
            dropdown: {
                position: "manual",
                maxItems: Infinity,
                enabled: 0,
                classname: "customSuggestionsList"
            },
            templates: {
                dropdownItemNoMatch() {
                    return 'Nothing Found';
                }
            },
            enforceWhitelist: true
    });

    var exclude = document.querySelector('input[name=exclude]'),
        excludeTagify = new Tagify(exclude, {
            userInput: true,
            whitelist: flagWhiteList,
            dropdown: {
                position: "manual",
                maxItems: Infinity,
                enabled: 0,
                classname: "customSuggestionsList"
            },
            templates: {
                dropdownItemNoMatch() {
                    return 'Nothing Found';
                }
            },
            enforceWhitelist: true
    });

    var export_format = document.querySelector('input[name=export_format]'),
        exportTagify = new Tagify(export_format, {
            userInput: false,
            whitelist: ["JSON", "CSV", "HTML"],
            dropdown: {
                position: "manual",
                maxItems: Infinity,
                enabled: 0,
                classname: "customSuggestionsList"
            },
            templates: {
                dropdownItemNoMatch() {
                    return 'Nothing Found';
                }
            },
            enforceWhitelist: true
    });

    function updateRPNameAPI() {
        rpNameTagify.dropdown.show();
        const rpNameValues = rpNameTagify.value.map(tag => tag.value);
        rp_name_tags_list.textContent = rpNameValues.join('+').replaceAll(' ', '_');
        if (!rp_name_tags_list.textContent){
            rp_name_tags_list.textContent = '{RP}';
        };
    }

    function updateSoftwareNameAPI() {
        softwareNameTagify.dropdown.show();
        const softwareNameValues = softwareNameTagify.value.map(tag => tag.value);
        software_name_tags_list.textContent = softwareNameValues.join('+').replaceAll(' ', '_');
        if (!software_name_tags_list.textContent){
            software_name_tags_list.textContent = '{SOFTWARE_NAME}';
        };
    }

    function updateIncludeAPI() {
        includeTagify.dropdown.show();
        const includeValues = includeTagify.value.map(tag => tag.value);
        include_tags_list.textContent = includeValues.join('+').replaceAll(' ', '_').toLowerCase();
        if (!include_tags_list.textContent){
            include_tags_list.textContent = '{INCLUDE}';
        };
    }

    function updateExcludeAPI() {
        excludeTagify.dropdown.show();
        const excludeValues = excludeTagify.value.map(tag => tag.value);
        exclude_tags_list.textContent = excludeValues.join('+').replaceAll(' ', '_').toLowerCase();
        if (!exclude_tags_list.textContent){
            exclude_tags_list.textContent = '{EXCLUDE}';
        };
    }

    function updateExportAPI() {
        exportTagify.dropdown.show();
        const exportValues = exportTagify.value.map(tag => tag.value);
        export_tags_list.textContent = exportValues.join('+').replaceAll(' ', '_');
        if (!export_tags_list.textContent){
            export_tags_list.textContent = '{FORMAT}';
        };
    }

    rpNameTagify.on('add', updateRPNameAPI)
    .on('remove', updateRPNameAPI)
    .on('change', updateRPNameAPI);

    softwareNameTagify.on('add', updateSoftwareNameAPI)
    .on('remove', updateSoftwareNameAPI)
    .on('change', updateSoftwareNameAPI);

    includeTagify.on('add', updateIncludeAPI)
    .on('remove', updateIncludeAPI)
    .on('change', updateIncludeAPI);

    excludeTagify.on('add', updateExcludeAPI)
    .on('remove', updateExcludeAPI)
    .on('change', updateExcludeAPI);

    exportTagify.on('add', updateExportAPI)
    .on('remove', updateExportAPI)
    .on('change', updateExportAPI);


    rpNameTagify.on("dropdown:show", onSuggestionsListUpdate)
    .on("dropdown:hide", onSuggestionsListHide)
    .on('dropdown:scroll', onDropdownScroll);

    softwareNameTagify.on("dropdown:show", onSuggestionsListUpdate)
    .on("dropdown:hide", onSuggestionsListHide)
    .on('dropdown:scroll', onDropdownScroll);

    includeTagify.on("dropdown:show", onSuggestionsListUpdate)
    .on("dropdown:hide", onSuggestionsListHide)
    .on('dropdown:scroll', onDropdownScroll);

    renderSuggestionsList();  // defined down below   

    // ES2015 argument destructuring
    function onSuggestionsListUpdate({ detail: suggestionsElm }) {
        console.log(suggestionsElm)
    }

    function onSuggestionsListHide() {
        console.log("hide dropdown")
    }

    function onDropdownScroll(e) {
        console.log(e.detail)
    }

    // https://developer.mozilla.org/en-US/docs/Web/API/Element/insertAdjacentElement
    function renderSuggestionsList() {
        rpNameTagify.dropdown.show() // load the list
        rpNameTagify.DOM.scope.parentNode.appendChild(rpNameTagify.DOM.dropdown)
        softwareNameTagify.dropdown.show() // load the list
        softwareNameTagify.DOM.scope.parentNode.appendChild(softwareNameTagify.DOM.dropdown)
        includeTagify.dropdown.show() // load the list
        includeTagify.DOM.scope.parentNode.appendChild(includeTagify.DOM.dropdown)
        excludeTagify.dropdown.show() // load the list
        excludeTagify.DOM.scope.parentNode.appendChild(excludeTagify.DOM.dropdown)
        exportTagify.dropdown.show() // load the list
        exportTagify.DOM.scope.parentNode.appendChild(exportTagify.DOM.dropdown)
    }

    // "remove all tags" button event listener
    document.getElementById('rpResetButton')
    .addEventListener('click', rpNameTagify.removeAllTags.bind(rpNameTagify));

    document.getElementById('softwareResetButton')
    .addEventListener('click', softwareNameTagify.removeAllTags.bind(softwareNameTagify));

    document.getElementById('includeResetButton')
        .addEventListener('click', includeTagify.removeAllTags.bind(includeTagify));

    document.getElementById('excludeResetButton')
        .addEventListener('click', excludeTagify.removeAllTags.bind(excludeTagify));
    
    document.getElementById('exportResetButton')
        .addEventListener('click', exportTagify.removeAllTags.bind(exportTagify));


    // Reset Include/Exclude when Toggle Radio Buttons
    document.getElementById('includeRadio')
        .addEventListener('click', excludeTagify.removeAllTags.bind(excludeTagify));
    document.getElementById('excludeRadio')
        .addEventListener('click', includeTagify.removeAllTags.bind(includeTagify));
    document.getElementById('ieNoneRadio')
        .addEventListener('click', includeTagify.removeAllTags.bind(includeTagify));
    document.getElementById('ieNoneRadio')
        .addEventListener('click', excludeTagify.removeAllTags.bind(excludeTagify));
    document.getElementById('rpRadio')
        .addEventListener('click', softwareNameTagify.removeAllTags.bind(softwareNameTagify));
    document.getElementById('softwareRadio')
        .addEventListener('click', rpNameTagify.removeAllTags.bind(rpNameTagify));

});