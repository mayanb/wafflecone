import React from 'react';
import ReactDOM from 'react-dom';
import { Autocomplete } from 'react-toolbox/lib/autocomplete';

export default class MaterialSelect extends React.Component {

 constructor() {
    super();
    this.handleMultipleChange = this.handleMultipleChange.bind(this);
    this.state = {
      multiple: [],
    };

  }

  handleMultipleChange(value) {
    this.setState({multiple: value});
  };

  render () {
    return (
      <div className="materialSelect">
        <Autocomplete
          direction="auto"
          onChange={this.handleMultipleChange}
          label="Choose processes"
          source={this.getSelect(this.props.options)}
          value={this.state.multiple}
        />
      </div>
    );
  }

  handleSelectChange(value) {
    this.setState({value : value})
  }

  getSelect(options) {
    if (!options)
      return;

    return Object.keys(options).map(function (key, i) {
      return options[key].name
    })

  }

}