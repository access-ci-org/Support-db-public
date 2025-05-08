//////////////////////////////////////////////////////
// Include/Exclude/None Radio Button Event Listener //
//////////////////////////////////////////////////////
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('include_exclude').addEventListener('click', function(event) {
        var include = document.getElementById('includeDiv');
        var exclude = document.getElementById('excludeDiv');
        var includeCurl = document.getElementById('includeCurl');
        var excludeCurl = document.getElementById('excludeCurl');
        var flag = document.querySelector("[name=includeRadioButtons]:checked").id;

        if (flag == "includeRadio"){
            include.style.display = "";
            exclude.style.display = "none";
            includeCurl.style.display = "";
            excludeCurl.style.display = "none";
        }
        else if (flag == "excludeRadio"){
            include.style.display = "none";
            exclude.style.display = "";
            includeCurl.style.display = "none";
            excludeCurl.style.display = "";
        }
        else if (flag == "ieNoneRadio"){
            include.style.display = "none";
            exclude.style.display = "none";
            includeCurl.style.display = "none";
            excludeCurl.style.display = "none";
        }
    });
});

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('rp_software').addEventListener('click', function(event) {
        var rp = document.getElementById('rpDiv');
        var software = document.getElementById('softwareDiv');
        var rpCurl = document.getElementById('rpCurl');
        var softwareCurl = document.getElementById('softwareCurl');
        var flag = document.querySelector("[name=rp_softRadioButtons]:checked").id;

        if (flag == "rpRadio"){
            rp.style.display = "";
            software.style.display = "none";
            rpCurl.style.display = "";
            softwareCurl.style.display = "none";
        }
        else if (flag == "softwareRadio"){
            rp.style.display = "none";
            software.style.display = "";
            rpCurl.style.display = "none";
            softwareCurl.style.display = "";
        }
    });
});