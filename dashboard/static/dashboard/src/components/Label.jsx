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

export {Label}