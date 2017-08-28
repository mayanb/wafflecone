import React from 'react'
import { fetch, requestID, ZeroState, post, put, del } from './APIManager.jsx'
import Activity from './ActivityLog-2.jsx'
import {Dialog} from './Dialog.jsx'
import $ from 'jquery'
import {Dropdown} from 'react-toolbox/lib/dropdown'
import update from 'immutability-helper'

export default class Dash extends React.Component {
  render() {
    return (
      <div>
        <Goals />
        <Activity />
      </div>
    )
  }
}

class Goals extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      addGoalDialog: false,
      editGoalDialog: -1,
      loading: false,
      lastRequestID: -1,
      goals: [],
    }
  }

  componentDidMount() {
    this.getGoals()
  }

  getGoals() {
    this.setState({loading: true})
    let url = window.location.origin + "/ics/goals/"
    let component = this

    let rID = requestID()
    this.lastRequestID = rID

    fetch(url, {team : window.localStorage.getItem("team") || "1"})
      .done(function (data) {
        if (component.lastRequestID != rID) 
          return

        component.setState({ goals: data })
      }).always(function () {
        if (component.lastRequestID != rID) 
          return
        component.setState({loading: false})
      })
  }

  handleAddGoal(index, newGoal, success, failure) {
    let url = window.location.origin + "/ics/goals/"
    let component = this
    let params = {
      "process_type": newGoal.processType.id, 
      "product_type": newGoal.productType.id,
      "goal": newGoal.goal || 0,
    }

    post(url, params)
      .done(function (data) {
        let ns = update(component.state.goals, {$push: [data]})
        component.setState({goals : ns}, success)
      })
      .fail(function (jqxhr, text, error) {
        failure()
      })
  }

  handleEditGoal(index, newGoal, success, failure) {
    let url = window.location.origin + "/ics/goals/edit/" + this.state.goals[index].id + "/"
    let component = this
    let params = {
      process_type: newGoal.processType.id, 
      product_type: newGoal.productType.id,
      goal: newGoal.goal
    }

    put(url, params)
      .done(function (data) {
        let ns = update(component.state.goals, {[index]: {$set: data}})
        component.setState({goals : ns}, success)
      })
      .fail(function (error) {
        failure()
      })
  }

  handleDeleteGoal(index) {
    let url = window.location.origin + "/ics/goals/edit/" + this.state.goals[index].id + "/"
    let component = this
    
    del(url)
      .done(function (data) {
        let ns = update(component.state.goals, {$splice: [[index, 1]]})
        component.setState({goals: ns})
      })
      .fail(function (error) {
        alert("Oops, something went wrong")
      })
  }

  render () {
    let addGoalDialog = false
    if (this.state.addGoalDialog) {
      addGoalDialog = <AddGoalDialog 
        onCancel={() => this.setState({addGoalDialog: false})} 
        onSubmit={this.handleAddGoal.bind(this)}
        goalIndex={-1}
      />
    }

    let editGoalDialog = false;
    if (this.state.editGoalDialog >= 0) {
      editGoalDialog = <AddGoalDialog 
        onCancel={() => this.setState({editGoalDialog: -1})} 
        onSubmit={this.handleEditGoal.bind(this)} 
        goalIndex={this.state.editGoalDialog}
        goal={this.state.goals[this.state.editGoalDialog]}
      />
    }

    return (
      <div className="goals page mini">
        {addGoalDialog}
        {editGoalDialog}
        <div className="page-header">
          <h2>Production Goals</h2>
          <button className="add-goal-button" onClick={() => this.setState({addGoalDialog: true})}>Add a new goal</button>
        </div>
        {
          this.state.goals.map(function (goal, i) {
            return <Goal 
              goal={goal} 
              key={i} 
              onEditGoal={() => this.setState({editGoalDialog: i})}
              onDeleteGoal={() => this.handleDeleteGoal(i)}
            />
          }, this)
        }
      </div>
    )
  }
}

/* getDisplayProportions
 * ---------------------
 * Takes a @goal object and extracts display requirements. 
 * Returns an object with the following fields:
 * @achieved: whether the goal has been met or not
 * @proportion: a ratio between actual and goal, order depends 
 *              on which is smaller, since we have to mark out
 *              the smaller one on a scale of the larger one
 */

function getDisplayProportions(g) {
  let actual = parseFloat(g.actual || 0)
  let goal = parseFloat(g.goal)

  if (actual < goal) {
    return {
      achieved: false,
      proportion: (goal ? Math.max(actual/goal * 100, 3) : 100)
    }
  } else {
    return { 
      achieved: true, 
      proportion: (actual ? Math.max(goal/actual * 100, 3) : 100)
    }
  }
}

function Goal(props) {
  let {achieved, proportion} = getDisplayProportions(props.goal)
  return (
    <div className="goal">

      <div className="goal-details">
        <div className="goal-details-left">
          <span className="product">{props.goal.process_name + " " + props.goal.product_code}</span>
          <span>{`${parseInt(props.goal.actual)}/${parseInt(props.goal.goal)} ${props.goal.process_unit.toUpperCase()}(S)`}</span>
        </div>
        <div className="goal-details-right goal-buttons">
          <button onClick={props.onEditGoal}><i className="material-icons">mode_edit</i></button>
          <button onClick={props.onDeleteGoal}><i className="material-icons">delete_forever</i></button>
        </div>
      </div>
      <div className={"goal-whole-bar " + (achieved?"goal-achieved":"")}>
        <div className="goal-filled-bar" style={{flex: (proportion + '%')}}>
          {parseInt(achieved?props.goal.goal:props.goal.actual) || 0}
        </div>
        <div style={{flex: ((100 - proportion) + '%')}}> 
          {parseInt(achieved?props.goal.actual:props.goal.goal) || 0}
        </div>
      </div>
      <div className="goal-buttons">
      </div>
    </div>
  )
}

class AddGoalDialog extends React.Component {
  constructor(props) {
    super(props) 
    this.state = {
      loading: false,
      done: false,
      processType: null,
      productType: null,
      goal: "",
      goal_unit: "",
      setup: false, 
      processes: [],
      products: []
    }
  }

  componentDidMount() {
    this.getProductsAndProcesses()
  }

  getProductsAndProcesses() {
    let thisObj = this
    let goal = this.props.goal
    let container = {}
    let defs = [this.getDeferred("processes", container), this.getDeferred("products", container)]

    $.when.apply(null, defs).done(function() {
      container.setup = true
      container.processType = container.processes[0].value
      container.productType = container.products[0].value 

      // if there was an existing goal that we are editing, 
      // set the form values to the existing goal
      if (goal) {
        container.processType = container.processes.find(function (e) {return e.value.id == goal.process_type}).value
        container.productType = container.products.find(function (e) {return e.value.id == goal.product_type}).value
        container.goal = parseInt(goal.goal)
      }

      thisObj.setState(container)
    })
  }

  getDeferred(keyword, container) {
    var deferred = $.Deferred();
    var req = {created_by: (window.localStorage.getItem("team") || "1")}
    if (!req.created_by) {
      alert("No teams loaded:(((")
    }

    $.get(window.location.origin + "/ics/" + keyword, req)
      .done(function (data) {
        container[keyword] = data.map(function (x) { return {value: x, label: x.name}})
        deferred.resolve()
      })
    return deferred.promise()
  }

  handleAddGoal() {
    this.setState({loading: true})
    let component = this

    this.props.onSubmit(this.props.goalIndex, this.state, function () {
      component.setState({done: true, error: false})
    }, function () {
      component.setState({error: true})
    })
  }

  handleChange(which, val) {
    this.setState({[which] : val})
  }

  render () {
    let title = (this.props.goal)? "Edit goal" : "Add a new goal"

    if (this.state.error) {
      return (
        <Dialog>
          <span className="dialog-title">{title}</span>
          <span className="dialog-text">Oops, something went wrong.</span>
          <div className="dialog-actions">
            <button className="dialog-button dialog-cancel" onClick={this.props.onCancel}>OK</button>
          </div>
        </Dialog>
      )
    }
    if (!this.state.setup) {
      return (
        <Dialog>
          <span className="dialog-title">{title}</span>
          <span className="dialog-text">Hang on a sec...</span>
          <div className="dialog-actions">
            <button className="dialog-button dialog-cancel" onClick={this.props.onCancel}>OK</button>
          </div>
        </Dialog>
      )
    } else if (this.state.done) {
      return (
        <Dialog>
          <span className="dialog-title">{title}</span>
          <span className="dialog-text">{this.props.goal?"Yay! Your goal has been updated.":"Yay! You added a new goal!"}</span>
          <div className="dialog-actions">
            <button className="dialog-button dialog-cancel" onClick={this.props.onCancel}>OK</button>
          </div>
        </Dialog>
      )
    } else {
      return (
        <Dialog>
          <span className="dialog-title">{title}</span>
          <div className="dialog-text">
            <div className="row">
              <div className="addgoal-field">
                <Dropdown
                  source={this.state.processes}
                  onChange={(val) => this.handleChange("processType", val)}
                  value={this.state.processType}
                />
              </div>
              <div className="addgoal-field">
                <Dropdown
                  source={this.state.products}
                  onChange={(val) => this.handleChange("productType", val)}
                  value={this.state.productType}
                />
              </div>
            </div>
            <div className="row">
              <div className="addgoal-field">
                <input type="text" placeholder="0" value={this.state.goal} onChange={(e) => this.handleChange("goal", e.target.value)} />
              </div>
              <span>{this.state.processType ? this.state.processType.unit : "unit(s)"}</span>
            </div>
          </div>
            <div className="dialog-actions">
              <button className="dialog-button dialog-cancel" style={{display: this.state.loading?"none":""}} onClick={this.props.onCancel}>Cancel</button>
              <button className="dialog-button" onClick={this.handleAddGoal.bind(this)}>{this.state.loading?"Adding goal...":"Confirm"}</button>
            </div>
        </Dialog>
      )
    }
  return false;
  }

}




