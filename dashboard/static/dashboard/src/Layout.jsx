import React from 'react';
import ReactDOM from 'react-dom';

export const Navbar = (props) => (
  <div className="navbar">
  	<div className="content-area">
  		<div className="nav">
		    <h1>{props.title}</h1>
	    	<h1>{props.title2}</h1>
	    </div>
	</div>
  </div>
)
