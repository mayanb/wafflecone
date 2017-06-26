import React from 'react';
import $ from 'jquery';
import moment from 'moment';
import Draggable, {DraggableCore} from 'react-draggable'; 
import update from 'immutability-helper';
import {icon} from './Task.jsx'

let connectionBlue = "#2196F3"

export default class FactoryMap extends React.Component {

  constructor(props) {
    super(props)
    this.handleStop = this.handleStop.bind(this)
    this.handleConnectionEnd = this.handleConnectionEnd.bind(this)
    this.handleConnectionDelete = this.handleConnectionDelete.bind(this)
    this.setDimensions = this.setDimensions.bind(this)
    this.state = {
      processes: [], 
      connections: [],
      selectedProcess: -1,
      selectedConnection: -1,
      height: 0,
      width: 0,
    }
  }

  render() {
    var thisObj = this

    if (this.state.processes.length == 0) {
      return (<svg className="factorymap" style={{width: this.state.width, height: this.state.height, backgroundColor: "green"}} /> )
    }

    return (
      <svg className="factorymap" style={{width: this.state.width, height: this.state.height, backgroundColor: "#1565C0"}} >

      <defs>
        <filter id="f3" x="0" y="0" width="200%" height="200%">
          <feOffset result="offOut" in="SourceAlpha" dx="2" dy="2" />
          <feGaussianBlur result="blurOut" in="offOut" stdDeviation="2" />
          <feBlend in="SourceGraphic" in2="blurOut" mode="normal" />
          <feColorMatrix values="1 0 0 0 0   1 0 0 0 0   1 0 0 0 0  1 0 0 0.4 0" type="matrix" in="shadowBlurOuter1"></feColorMatrix>
        </filter>

        <marker id="bluearrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M4,0 L0,3 L4,6 " stroke={connectionBlue} fill="transparent" />
        </marker>

        <marker id="redarrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M4,0 L0,3 L4,6 " stroke={"red"} fill="transparent" />
        </marker>

      </defs>
      {
        Object.keys(this.state.connections).map(function (cid) {
          let connection = this.state.connections[cid]
          if (connection == undefined) 
            return false

          let p1 = this.state.processes[connection.process_type]
          let p2 = this.state.processes[connection.recommended_input]

          return <DirectedLine 
            p1={this.unscale(p1)} p2={this.unscale(p2)} 
            p1Width={width(p1)} p2Width={width(p2)} 
            {...connection} key={cid}
            selected={cid==this.state.selectedConnection}
            onClick={() => this.selectConnection(cid)}
          />
        }, this)
      }
      {
        Object.keys(this.state.processes).map(function (pid) {
          let p = thisObj.state.processes[pid]
          if (p == undefined) 
            return false
          let coords = this.unscale(p)
          //let newp = update(p, {$merge: coords})
          return <ProcessTile 
            width={width(p)} height={40} 
            {...p} nx={coords.x} ny={coords.y} key={pid}
            selected={pid==this.state.selectProcess} 
            onStop={(e, ui) => this.handleStop(e, ui, pid)}
            onConnectionEnd={(x, y) => this.handleConnectionEnd(pid, x, y)}
            onClick={() => this.selectProcess(pid)}
          />
        }, this)
      }
      </svg>
    )
  }

  selectProcess(pid) {
    let ns = update(this.state, {$merge: {selectedConnection: -1, selectedProcess: pid} })
    this.setState(ns)
  }

  selectConnection(cid) {
    let ns = update(this.state, {$merge: {selectedConnection: cid, selectedProcess: -1} })
    this.setState(ns)
  }

  componentWillMount() {
    this.setDimensions()
  }

  setDimensions() {
    this.setState({height: $(window).height() - 64, width: $(window).width()})
  }

  componentDidMount() {
    let thisObj = this
    var container = {}
    let defs = [this.getProcesses(container), this.getConnections(container)]

    $.when.apply(null, defs).done(function() {
      thisObj.setState(container)
    })

    let url = window.location.origin + '/ics/recommendedInputs/'
    window.addEventListener('keyup', this.handleConnectionDelete)
    window.addEventListener('resize', this.setDimensions)
  }

  handleConnectionDelete(e) {
    let thisObj = this

    if (e.key == "Backspace" && this.state.selectedConnection != -1) {

      let url = window.location.origin + "/ics/recommendedInputs/" + this.state.selectedConnection + "/"
      $.ajax({method: "DELETE", url: url})
        .done(function (e) {
          let ns = update(thisObj.state, {
            connections: {
              $merge: {
                [thisObj.state.selectedConnection] : undefined 
              }
            }, selectedConnection: {$set: -1}
          })
          thisObj.setState(ns)
        })
    }

  }

  getProcesses(container) {
    var deferred = $.Deferred();
    var req = {created_by: (window.localStorage.getItem("team") || "1")}
    if (!req.created_by) {
      alert("No teams loaded:(((")
    }

    $.get(window.location.origin + "/ics/processes/", req)
      .done(function (data) {
        var processes = {}
        data.map(function (p, i) {
          processes[p.id] = p 
        })
        container.processes = processes
        deferred.resolve()
      })
    return deferred.promise()
  }

  getConnections(container) {
    var deferred = $.Deferred();
    var req = {created_by: (window.localStorage.getItem("team") || "1")}
    if (!req.created_by) {
      alert("No teams loaded:(((")
    }

    $.get(window.location.origin + "/ics/recommendedInputs/", req)
      .done(function (data) {
        console.log(data)
        var connections = {}
        data.map(function (c, i) {
          connections[c.id] = c 
        })
        container.connections = connections
        deferred.resolve()
      })
    return deferred.promise()
  }

  handleStop(e, ui, id) {
    this.forceUpdate()
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
  

  handleConnectionEnd(id, x, y) {
    var found = -1
    var o = this.unscale(this.state.processes[id])

    Object.keys(this.state.processes).map(function (pid) {
      let p = this.state.processes[pid]
      let n = this.unscale(p)
      let w = width(p)

      if (pid == id) return

      if (Math.abs(parseFloat(x)+o.x-(n.x + w/2)) <= w/2+10 && Math.abs(parseFloat(y)+o.y-(n.y+10)) <= 20) {
        found = pid
      }
    }, this)

    if (found == -1) 
      return

    Object.keys(this.state.connections).map(function (cid) {
      var c = this.state.connections[cid]
      if (c && c.process_type == id && c.recommended_input == found) 
        found = -1
    }, this)

    if (found == -1)
      return

    var nc = {process_type: found, recommended_input: id}
    this.makeNewConnection(this, nc)
  }

  makeNewConnection(thisObj, data) {
    let url = window.location.origin + '/ics/recommendedInputs/'
    $.ajax({ url: url, data: data, method: 'POST' })
      .done(function (d) {
        var obj = {}
        obj[d.id] = d
        var ns = update(thisObj.state, {connections : { $merge: obj }})
        thisObj.setState(ns)
      })
  }

  scale(coords) {
    let h = this.state.height
    let w = this.state.width

    let x = parseFloat(coords.x)
    let y = parseFloat(coords.y)

    let v = {x: trim(coords.x/w*100), y: trim(coords.y/h*100)}

    return v

  }

  unscale(coords) {
    let h = this.state.height
    let w = this.state.width

    let x = parseFloat(coords.x)
    let y = parseFloat(coords.y)

    let v = {x: x/100*w, y: y/100*h}
    return v
  }

  handleDelete(cid) {
    let url = window.location.origin + "/ics/recommendedInputs/" + cid + "/"
    $.ajax({url: url, method: "DELETE"}).done(function () {
      var ns = update(this.state, {connections: {$merge: {cid: undefined }}})
      this.setState(ns)
    })
  }

}

function trim(n) {
  return Math.floor(n * 1000)/1000
}

class DirectedLine extends React.Component {
  constructor(props) {
    super(props)
  }

  getMidPoint() {
    var halfLength = this.path.getTotalLength() * 2/3
    var p1 = this.path.getPointAtLength(halfLength-4)
    var p2 = this.path.getPointAtLength(halfLength+4)
    this.sample.setAttribute("x1", p1.x)
    this.sample.setAttribute("y1", p1.y)
    this.sample.setAttribute("x2", p2.x)
    this.sample.setAttribute("y2", p2.y)
    }

  componentDidMount() {
    this.getMidPoint()
  }

  componentWillReceiveProps(np) {
    this.getMidPoint()
  }

  render() {
    let x1 = this.props.p1.x + this.props.p1Width/2
    let y1 = this.props.p1.y + 40/2
    let x2 = this.props.p2.x + this.props.p2Width/2
    let y2 = this.props.p2.y + 40/2
    let path = `M${x1} ${y1} C ${x1} ${y1}, ${x2} ${y2}, ${x2} ${y2}`
    return (
      <g>
        <path
          d={path} 
          stroke={this.props.selected?"red":connectionBlue} strokeWidth="4" fill="transparent"
          ref={(path) => { this.path = path; }}
          onClick={this.props.onClick}
        />
        <line ref={(line) => { this.sample = line; }} strokeWidth="4" markerEnd={this.props.selected?"url(#redarrow)":"url(#bluearrow)"} />
      </g>
    )
  }

}


function ProcessTile(props) {
  return (
    <Draggable onDrag={(e, ui) => props.onStop(e, ui) } defaultPosition={{x: props.nx, y: props.ny}}>
      <g>
        <DraggableLine className="connectionTemp" x={props.width} y={props.height/2} onStop={(x, y) => props.onConnectionEnd(x, y)}/>
        <rect className="processTile" width={props.width} height={props.height} rx="4" ry="4" filter="url(#f3)"/>
        <image x={10} y={10} height={20} width={20} xlinkHref={icon(props.icon)} />
        <text textAnchor="middle" x={(props.width-25)/2 + 25} y={props.height/2+4}>{props.name + " (" + props.code + ")"}</text>
        
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
          <line {...this.state} stroke="#1976D2" strokeWidth="4" strokeDasharray="8, 8"/>
          <rect x={this.props.x-2} y={this.props.y} height="15" width="15" rx="2" ry="2" style={{fill: "#64B5F6"}}/>
        </g>
      </DraggableCore>
    )
  }


}

function  width(p) {
  return ((p.name.length + p.code.length + 5) * 7) + 25
}