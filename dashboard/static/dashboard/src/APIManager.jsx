import React from 'react'

import $ from 'jquery'

function fetch(url, params) {
  let team = window.localStorage.getItem("team") || "1"
  params.team = team
  return $.get(url, params)
}

function post(url, params) {
  return $.ajax({
    method: "POST",
    url: url,
    data: params,
    contentType: 'application/json',
    processData: false,
  })
}

function requestID() {
  return Math.floor(Math.random() * 1000)
}

function ZeroState(props) {
  var sentence = "Looks like there's nothing here!"
  if (props.filtered) {
    sentence = "Looks like there's nothing here. Try expanding your search."
  }
  return (
    <div className="zero-state">
      <span>{sentence}</span>
    </div>
  )
}


export { fetch, requestID, ZeroState, post }