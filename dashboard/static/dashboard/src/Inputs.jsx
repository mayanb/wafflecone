import React from 'react';
import ReactDOM from 'react-dom';
import Select from 'react-select';
import Datepicker from './Datepicker.jsx'
import WrapMenu from './WrapMenu.jsx'

class Multiselect extends React.Component {

 constructor() {
    super();
    this.handleMultipleChange = this.handleMultipleChange.bind(this);
    this.state = {
      value: [],
    };

  }

  handleMultipleChange(value) {
    this.setState({value: value});
  };

  render () {
    return (
      <div className="multiselect">
        <Select multi
          name="form-field-name"
          value={this.state.value}
          options={this.getSelect(this.props.options)}
          onChange={this.handleMultipleChange}
          placeholder={this.props.placeholder}
          clearable={false}
        />
      </div>
    );
  }

  getSelect(options) {
    if (!options)
      return;

    return Object.keys(options).map(function (key, i) {
      return {value: options[key].id, label: options[key].name}
    })

  }

}

class Filters extends React.Component {

  constructor() {
    super();
    this.handleInventoryChange = this.handleInventoryChange.bind(this);
    this.state = {
      inventory: false
    }
  }

  handleInventoryChange() {
    this.setState({inventory: !this.state.inventory })
  }

  render () {
    return (
      <div className="filters card">
        <h1>Show me...</h1>

        <div>
          <Multiselect options={this.props.processes} placeholder="All processes" />
          <Multiselect options={this.props.products} placeholder="All products" />
        </div>

        <div>
          <input type="checkbox" onChange={this.handleInventoryChange} value={this.state.inventory}/>
          <p> Show current inventory </p>
        </div>

        <div style={{ display: this.state.inventory ? "none" : "initial" }}>
          <h1>Created between...</h1>
          <div>
            <Datepicker />
          </div>
        </div>

      </div>
    );
  }
}

export { Filters };