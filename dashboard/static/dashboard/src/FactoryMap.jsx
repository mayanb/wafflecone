import React from 'react';
import $ from 'jquery';
import moment from 'moment';
import Draggable, {DraggableCore} from 'react-draggable'; 
import update from 'immutability-helper';

export default class FactoryMap extends React.Component {

  constructor(props) {
    super(props)
    this.handleStop = this.handleStop.bind(this)
    this.handleConnectionEnd = this.handleConnectionEnd.bind(this)
    this.state = {
      processes: [], 
      connections: [
        {id: 1, process_type: 2, reccommended_input: 14}, 
        {id: 2, process_type: 15, reccommended_input: 14},
        {id: 3, process_type: 12, reccommended_input: 14},
        {id: 4, process_type: 13, reccommended_input: 14},
      ],
      selectedProcess: -1,
      selectedConnection: -1
    }
  }

  render() {
    var thisObj = this

    if (this.state.processes.length == 0) {
      return (<svg style={{width: "100%", height: "100%", backgroundColor: "green"}} /> )
    }

    return (
      <svg style={{width: "100%", height: "100%", backgroundColor: "#1565C0"}}>

      <defs>
        <filter id="f3" x="0" y="0" width="200%" height="200%">
          <feOffset result="offOut" in="SourceAlpha" dx="2" dy="2" />
          <feGaussianBlur result="blurOut" in="offOut" stdDeviation="2" />
          <feBlend in="SourceGraphic" in2="blurOut" mode="normal" />
          <feColorMatrix values="1 0 0 0 0   1 0 0 0 0   1 0 0 0 0  1 0 0 0.4 0" type="matrix" in="shadowBlurOuter1"></feColorMatrix>
        </filter>
      </defs>
      {

        Object.keys(this.state.connections).map(function (cid) {
          let connection = this.state.connections[cid]
          let p1 = this.unscale(this.state.processes[connection.process_type])
          let p2 = this.unscale(this.state.processes[connection.reccommended_input])
          return <line x1={p1.x+50} y1={p1.y+50} x2={p2.x+50} y2={p2.y+50} key={connection.id} strokeWidth="2" stroke="orange"/>
        }, this)
      }
      {
        Object.keys(this.state.processes).map(function (pid) {
          let p = thisObj.state.processes[pid]
          let coords = thisObj.unscale(p)
          let newp = update(p, {$merge: coords})
          return <ProcessTile width={120} height={100} {...newp} key={pid} onStop={(e, ui) => thisObj.handleStop(e, ui, pid)}
            onConnectionEnd={(x, y) => thisObj.handleConnectionEnd(pid, x, y)} />
        })
      }
      </svg>
    )
  }

  componentDidMount() {
    var thisObj = this
    $.get(window.location.origin + "/ics/processes/")
      .done(function (data) {
        var processes = {}
        data.map(function (p, i) {
          processes[p.id] = p 
        })
        thisObj.setState({processes: processes})
      })
  }

  handleStop(e, ui, id) {
    let url = window.location.origin + "/ics/processes/move/" + id + "/"
    let p = this.state.processes[id]
    let data = this.scale({ x: ui.x, y:  ui.y})
    let thisObj = this

    $.ajax({url: url, method: 'PUT', data: data}).done(function (responseData) {
      var newState = update(thisObj.state, {processes: 
                          { [id] : 
                            { $merge:  
                              {x: responseData.x, y: responseData.y } 
                            } 
                          } 
                        })
      thisObj.setState(newState)
    })
  }

  handleConnectionStart(e, ui) {
    console.log("Starting a connection!")
  }

  

  handleConnectionEnd(id, x, y) {
    var found = -1
    var o = this.unscale(this.state.processes[id])

    Object.keys(this.state.processes).map(function (pid) {
      var n = this.unscale(this.state.processes[pid])
      if (pid == 11)
        console.log(Math.abs(parseFloat(x)+o.x-n.x-50) + " " + Math.abs(parseFloat(y)+o.y-n.y-50))
      if (Math.abs(parseFloat(x)+o.x-n.x-50) < 60 && Math.abs(parseFloat(y)+o.y-n.y-50) < 60) {
        found = pid
      }
    }, this)

    if (found == -1) 
      return

    Object.keys(this.state.connections).map(function (cid) {
      var c = this.state.connections[cid]
      if (c.process_type == id && c.reccommended_input == found) 
        found = -1
    }, this)

    if (found == -1)
      return

    var nc = {id: this.state.connections.length+1, process_type: id, reccommended_input: found}
    var ns = update(this.state, {connections : { $push: [nc] }})
    this.setState(ns)
  }

  scale(coords) {
    let h = $('svg').height()
    let w = $('svg').width()

    let x = parseFloat(coords.x)
    let y = parseFloat(coords.y)

    let v = {x: trim(coords.x/w*100), y: trim(coords.y/h*100)}

    return v

  }

  unscale(coords) {
    let h = $('svg').height()
    let w = $('svg').width()

    let x = parseFloat(coords.x)
    let y = parseFloat(coords.y)

    let v = {x: x/100*w, y: y/100*h}
    return v
  }

}

function trim(n) {
  return Math.floor(n * 1000)/1000
}


function ProcessTile(props) {
  return (
    <Draggable onDrag={(e, ui) => props.onStop(e, ui) } defaultPosition={{x: props.x, y: props.y}}>
      <g>
        <DraggableLine x={props.width} y={props.height/2} onStop={(x, y) => props.onConnectionEnd(x, y)}/>
        <rect className="processTile" width={props.width} height={props.height} rx="4" ry="4" filter="url(#f3)"/>
        <text textAnchor="middle" x={props.width/2} y={props.height-10}>{props.name}</text>
        
      </g>
    </Draggable>
    )
}

class DraggableLine extends React.Component {
  constructor(props) {
    super(props)
    this.handleDrag = this.handleDrag.bind(this)
    this.handleDragStop = this.handleDragStop.bind(this)
    this.state = { x1: props.x+5, y1: props.y+5, x2: props.x+5, y2: props.y+5 }
  }

  handleDrag(): Function {
    return (e: SyntheticEvent | MouseEvent, {node, deltaX, deltaY}: DragCallbackData) => {
      e.stopImmediatePropagation()

      let state = update(this.state, {$merge: {x2: this.state.x2 + deltaX, y2: this.state.y2 + deltaY}})
      this.setState(state)
    }
  }

  handleDragStop(): Function {
    return (e: SyntheticEvent | MouseEvent, {node, deltaX, deltaY}: DragCallbackData) => {
      this.props.onStop(this.state.x2, this.state.y2)
      let state = update(this.state, {$merge: {x2: this.props.x+5, y2: this.props.y+5}})
      this.setState(state)
    }
  }

  componentWillReceiveProps(props) {
    this.setState({ x1: props.x+5, y1: props.y+5, x2: props.x+5, y2: props.y+5 } )
  }

  render() {
    return (
      <DraggableCore onDrag={this.handleDrag()} onStop={this.handleDragStop()}>
        <g>
          <rect x={this.props.x-2} y={this.props.y} height="15" width="15" rx="2" ry="2" style={{fill: "#64B5F6"}}/>
          <line {...this.state} stroke="black" strokeWidth="2" />
        </g>
      </DraggableCore>
    )
  }


}
