import React from 'react'
import ReactDOM from 'react-dom'
import {NavLink} from 'react-router-dom'

const Navbar = (props) => (
  <div className="navbar">
  	<div className="content-area">
  		<div className="left">
	  		<h1>Scoop</h1>
	  	</div>
	  	<div className="nav center">
	  		<ul>
		    { props.options.map(function (x, i) {
		    	return (
            <li key={i}> 
              <NavLink exact to={ "/dashboard/" + props.links[i]} activeClassName="active">{x}</NavLink>
            </li>
          )
		    })}
		    </ul>
	  	</div>
  		<div className="right">
  			<p>Production</p>
	    </div>
	</div>
  </div>
)

const ContentDescriptor = (props) => (
	<div className="content-descriptor">
		<div className="left">
			<p style={{ display: (props.count > 0)?"":"none" }}> Showing {props.startIndex}-{props.startIndex+props.count} results out of {props.total}. </p>
			<p style={{ display: (props.count > 0)?"none":"" }}> Looks like there's nothing here! Try changing your filters. </p>
		</div>
		<div className="right">
			<button style={{ display: props.previous?"":"none" }} onClick = { () => props.onPage(props.previous) }>Previous</button>
			<button style={{ display: props.next?"":"none" }} onClick = {() => props.onPage(props.next) }>Next</button>
		</div>
	</div>
)

export {Navbar, ContentDescriptor}