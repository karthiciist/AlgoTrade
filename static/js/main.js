var baseurl = "http://127.0.0.1:8099"

function authenticate(){

    let client_id = document.getElementById('clientid').value
    let client_secret = document.getElementById('clientsecret').value

    let form_data = new FormData()
    form_data.append('client_id', client_id)
    form_data.append('client_secret', client_secret)
    let url = baseurl + '/getauthcode'
    let response = fetch(url, {
        method : 'POST',
        body : form_data
    })

}

function adxbased(){
    var instrument_dropdown = document.getElementById("instrument");
    var value = instrument_dropdown.value;
    var text = instrument_dropdown.options[instrument_dropdown.selectedIndex].text;

    let form_data = new FormData()
    form_data.append('instrument', value)
    let url = baseurl + '/initiate_adx_trade'
    let response = fetch(url, {
        method : 'POST',
        body : form_data
    })

}