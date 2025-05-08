document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('enableRegex').addEventListener('click', function(event) {
        var regexCurl = document.getElementById('regexCurl');

        if (document.querySelector("[id=enableRegex]:checked"))
        {
            regexDiv.style.display="";
            regexCurl.style.display="";
        }
        else
        {
            regexDiv.style.display="none";
            regexForm.value="";
            regex_list.textContent="{REGEX}";
            regexCurl.style.display="none";
        }
    })

    document.getElementById('rp_soft_andor').addEventListener('click', function(event) {
        var rp_software = document.getElementById('rp_software');

        if (document.querySelector("[id=rp_soft_andor]:checked"))
        {
            rp_software.innerHTML = "+";
        }
        else
        {
            rp_software.innerHTML = "&";
        }
    })
});