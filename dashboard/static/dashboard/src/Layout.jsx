import React from 'react';
import ReactDOM from 'react-dom';

const Navbar = (props) => (
  <div className="navbar">
  	<div className="content-area">
  		<div className="left">
	  		<h1>Scoop @ bama </h1>
	  	</div>
  		<div className="nav right">
 			<ul>
		    { props.options.map(function (x, i) {
		    	return <li className={i==props.active?"active":""} /*onClick={ () => props.onNav(i) }*/  key={i}> 
		    		<a href={window.location.origin + "/dashboard/" + props.links[i]}>{x}</a> 
		    	</li>
		    })}
		    </ul>
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