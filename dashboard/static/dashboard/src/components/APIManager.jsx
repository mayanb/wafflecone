import React from 'react'
import $ from 'jquery'
import update from 'immutability-helper'

var refreshing = false

function fetch(url, params) {
  let team = window.localStorage.getItem("team") || "1"
  params.team = team
  return $.get(url, params)
}

function refreshToken() {

}

function post(url, params, headers) {

  while (refreshing) {
    
  }

  let req = {
    method: "POST",
    url: url,
    data: params,
  }

  if (headers) {
    req = update(req, {$merge: headers})
  }

  return $.ajax(req)
}

function put(url, params) {
  return $.ajax({
    method: "PUT",
    url: url,
    data: params, 
  })
}

function del(url) {
  return $.ajax({
    method: "DELETE",
    url: url
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


export { fetch, requestID, ZeroState, post, put, del }