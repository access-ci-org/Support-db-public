////////////////////////
// On-Submit API Call //
////////////////////////
// Allows for fetching information from the API
// and injecting the payload into the website
// without refreshing the page
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('API_Form').addEventListener('submit', function handleSubmit(event) {
        event.preventDefault();

        const formData = new FormData(document.getElementById('API_Form'));

        const API_KEY = document.getElementById('APIKeyCurl').innerText;
        const rp_list = encodeURIComponent(document.getElementById('rp_name_tags_list').innerText);
        const software_list = encodeURIComponent(document.getElementById('software_name_tags_list').innerText);
        const include_list = encodeURIComponent(document.getElementById('include_tags_list').innerText);
        const exclude_list = encodeURIComponent(document.getElementById('exclude_tags_list').innerText);

        var fetchLink = `https://localhost:5000/api/${API_KEY}/search=rp(${rp_list})&software_name(${software_list})`;
        var testLink = 'https://jsonplaceholder.typicode.com/posts/1'

        if (include_list != '%7BINCLUDE%7D'){
            fetchLink = fetchLink + '&include(' + include_list + `)`;
        }
        if (exclude_list != '%7BEXCLUDE%7D'){
            fetchLink = fetchLink + '&exclude(' + exclude_list + `)`;
        }

        fetch(testLink)
            .then(response => response.json())
            .then(responseJSON => {
                // Display response
                document.getElementById('formatted_query_output').innerText = JSON.stringify(responseJSON, null, 2);
                formData.append('Response', JSON.stringify(responseJSON));
                
                // Send the form data to the backend
                return fetch('/API', {
                    method: 'POST',
                    body: formData,
                });
            })
            // Parse JSON from the Flask response
            .then(postResponse => postResponse.json()) 
            .then(data => {
                var isOutputJson = data.json;
                var isOutputCsv = data.csv;
                var isOutputHtml = data.html;

                // Dynamically show the buttons based on the Flask response
                if (isOutputJson) {
                    document.getElementById('json_export').style.display = "block";
                } else {
                    document.getElementById('json_export').style.display = "none";
                }

                if (isOutputCsv) {
                    document.getElementById('csv_export').style.display = "block";
                } else {
                    document.getElementById('csv_export').style.display = "none";
                }

                if (isOutputHtml) {
                    document.getElementById('html_export').style.display = "block";
                } else {
                    document.getElementById('html_export').style.display = "none";
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alertFailure(error);
            });
        alertSuccess();
    });
});

/* Simple scripts that popup an alert on API call success/failure */
function alertSuccess()
{
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            Your request has been sent! Check below for your results!
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    // Auto-close the alert after 5 seconds
    setTimeout(function() {
        let alertNode = document.querySelector('.alert');
        if (alertNode) {
            alertNode.classList.remove('show');
            setTimeout(() => alertNode.remove(), 500); // Wait for fade-out
        }
    }, 5000);
}

function alertFailure(error)
{
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            Your request failed! Error: {{ error }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    // Auto-close the alert after 5 seconds
    setTimeout(function() {
        let alertNode = document.querySelector('.alert');
        if (alertNode) {
            alertNode.classList.remove('show');
            setTimeout(() => alertNode.remove(), 150); // Wait for fade-out
        }
    }, 5000);
}