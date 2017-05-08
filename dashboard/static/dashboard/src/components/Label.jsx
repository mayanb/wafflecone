import React from 'react';

function Label(props) {
  console.log(props)
  return (
    <svg className="labelSVG" width="431px" height="241px" viewBox="0 0 431 241" version="1.1" xmlns="http://www.w3.org/2000/svg">
      <defs></defs>
      <g id="process-icons" stroke="none" strokeWidth="1" fill="none" fillRule="evenodd">
        <g id="Artboard">
          <image id="hello" x="33.7644766" y="32.963" width="148.242811" height="148.242811"></image>
          <text id="R-ZZC-1010-2" fontFamily="Overpass" fontSize="25" fontWeight="bold" fill="#000000">
            <tspan x="206.385882" y="135.102905">{props.taskLabel || ""}</tspan>
          </text>
          <text id="ZZC" fontFamily="Overpass" fontSize="80" fontWeight="bold" lineSpacing="80" fill="#000000">
            <tspan x="206.385882" y="91">{props.originLabel}</tspan>
          </text>
          <text id="Here-are-some-notes" fontFamily="Overpass-Regular, Overpass" fontSize="19" fontWeight="normal" fill="#000000">
            <tspan x="206.385882" y="179.205811">{props.notesLabel}</tspan>
          </text>
          <path d="M36.885882,209 L404.527541,209" id="Line" stroke="#000000" strokeLinecap="square"></path>
          <rect id="Rectangle-4" fill="#FFFFFF" x="61.385882" y="193.037" width="93" height="32"></rect>
          <text id="48CND9" fontFamily="OverpassMono-Regular, Overpass Mono" fontSize="20" fontWeight="normal" fill="#000000">
            <tspan x="70.885882" y="216.037">{props.qrCode}</tspan>
          </text>
        </g>
      </g>
    </svg>
  )
}

function LabelV2(props) {
  return (
   <svg width="450px" height="247px" viewBox="0 0 5323 2918" version="1.1" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <style>
      @import url('https://fonts.googleapis.com/css?family=Overpass+Mono|Overpass:400,700');
      </style>
    </defs>
    <g id="Page-1" stroke="none" strokeWidth="1" fill="none" fill-rule="evenodd">
        <g id="Artboard">
            <g id="Group" transform="translate(0.000000, 282.001992)">
                <text textAnchor="middle" id="CV2" fontFamily="Overpass-Bold, Overpass" fontSize="742.250996" fontWeight="bold" fill="#000000">
                    <tspan x="3724" y="782.885835">CV2</tspan>
                </text>
                <text textAnchor="middle" id="RCS-0221-1" fontFamily="Overpass-Bold, Overpass" fontSize="424.143426" fontWeight="bold" fill="#000000">
                    <tspan x="3724" y="1541.43574">RCS-0221-1</tspan>
                </text>
                <rect id="Rectangle" fill="#E9E9E9" x="434.747012" y="265.089641" width="1272.43028" height="1272.43028"></rect>
                <text id="3ba1ae" fontFamily="OverpassMono-Regular, Overpass Mono" fontSize="212.071713" fontWeight="normal" fill="#000000">
                    <tspan x="679.053625" y="2286.30279">3ba1ae</tspan>
                </text>
                <path d="M5.30179283,1807.91135 L5317.86752,1807.91135" id="Line" stroke="#979797" strokeWidth="10.6035857" stroke-linecap="square"></path>
                <path d="M3560.23854,997.604958 L3891.51594,997.604958" id="Line" stroke="#979797" strokeWidth="10.6035857" stroke-linecap="square"></path>
                <text textAnchor="middle" id="RCS-CV2-0221-1" fontFamily="OverpassMono-Regular, Overpass Mono" fontSize="212.071713" fontWeight="normal" fill="#000000">
                    <tspan x="3724" y="2286.30279">RCS-0221-1</tspan>
                </text>
            </g>
        </g>
    </g>
</svg>
  )
}

export {Label, LabelV2}