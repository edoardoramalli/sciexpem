import React from 'react';
import ReactDOM from 'react-dom';
import {message, Tag, Button, Menu, Dropdown, Icon, Table, Divider, Card, Alert, Popconfirm} from 'antd';
import './index.css';
//import App from './App';
import registerServiceWorker from './registerServiceWorker';


import ReactTable from "react-table";
import "react-table/react-table.css";
import axios from 'axios';
import matchSorter from 'match-sorter';
import 'antd/dist/antd.css';  // or 'antd/dist/antd.less'
import 'react-table/react-table.css'
import {DataTable} from 'antd-data-table'

import ReactChartkick, {LineChart, PieChart} from 'react-chartkick'
import Chart from 'chart.js'
import {Line} from 'react-chartjs-2';
import Plot from 'react-plotly.js';


import {WrappedCommonPropertiesForm} from "./Input";

import {InitialSpeciesList, SearchAndExecute, CommonPropertiesList, SearchMain, CurveMatchingResult} from "./Search"
import {GenericMultiDraw} from "./Components";



ReactChartkick.addAdapter(Chart)

String.prototype.format = function () {
    let a = this;
    for (let k in arguments) {
        a = a.replace("{" + k + "}", arguments[k])
    }
    return a
};





class ActionCell extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            loadingDelete : false,
        }
    }

    handleDelete = (e) => {
        const e_id = this.props.e_id;
        this.setState({loadingDelete : true});
        axios.delete('experimentmanager/api/experiment/' + e_id.toString())
            .then(res => {
                this.props.handleDelete(e_id);
                this.setState({loadingDelete : false})

            }).catch(error => {
            console.log(error.response)

        });
    };

    handleClick = (e) => {
        let exp_id = this.props.e_id;
        let file_doi = this.props.file_doi;
        if (e.key === 'opensmoke') {

            const request_url = 'experimentmanager/api/experiment/download/input_file/' + exp_id.toString();
            axios.get(request_url, {
                responseType: 'blob',
                timeout: 30000
            })
                .then(res => {
                    const url = window.URL.createObjectURL(new Blob([res.data]));
                    const link = document.createElement('a');
                    link.href = url;

                    const file_name = file_doi + ".dic"
                    link.setAttribute('download', file_name);

                    document.body.appendChild(link);
                    link.click();
                    message.success('Opensmoke input file downloaded')
                })
                .catch(function (error) {
                    // handle error
                    console.log(error);
                    message.error('Error')
                })
        }

        else if (e.key === 'excel') {

            const request_url = '127.0.0.1:8000/experimentmanager/api/experiment/download/excel/' + exp_id.toString();
            axios.get(request_url, {
                responseType: 'blob',
                timeout: 30000
            })
                .then(res => {
                    const url = window.URL.createObjectURL(new Blob([res.data]));
                    const link = document.createElement('a');
                    link.href = url;

                    const file_name = file_doi + ".xlsx"
                    link.setAttribute('download', file_name);

                    document.body.appendChild(link);
                    link.click();
                    message.success('Excel file downloaded')
                })
                .catch(function (error) {
                    // handle error
                    console.log(error);
                    message.error('Error')
                })
        }

        else if (e.key == "xml"){
            const request_url = 'experimentmanager/api/experiment/download/input_file/' + exp_id.toString();
            axios.get(request_url, {
                responseType: 'blob',
                timeout: 30000
            })
                .then(res => {
                    const url = window.URL.createObjectURL(new Blob([res.data]));
                    const link = document.createElement('a');
                    link.href = url;

                    const file_name = file_doi + ".dic"
                    link.setAttribute('download', file_name);

                    document.body.appendChild(link);
                    link.click();
                    message.success('Opensmoke input file downloaded')
                })
                .catch(function (error) {
                    // handle error
                    console.log(error);
                    message.error('Error')
                })
        }


    };

    render() {
        const menu = (
            <Menu onClick={this.handleClick}>
                <Menu.Item key="xml">XML Respecth</Menu.Item>
                <Menu.Item key="excel">Excel</Menu.Item>
                <Menu.Item key="opensmoke">Opensmoke input</Menu.Item>
            </Menu>
        );

        return (
            <div>
                <Dropdown overlay={menu}>
                    <Button shape="circle" icon="download">
                    </Button>
                </Dropdown>
                <Popconfirm title="Are you sure delete this experiment?" onConfirm={this.handleDelete} okText="Yes"
                            cancelText="No">
                    <Button shape="circle" icon="delete" loading={this.state.loadingDelete}>
                    </Button>
                </Popconfirm>
            </div>

        )
    }
}


class ExperimentDraw extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            response: {},
            error: null,

        }
    }

    render() {
        if (this.state.error) {
            return (
                <Alert message={this.state.error.data} type="warning" />
            )
        }

        return (
            <GenericMultiDraw response={this.state.response}/>
        );
    }

    componentDidMount() {
        const exp_id = this.props.experiment.id;

        axios.get('experimentmanager/api/experiment/curves/' + exp_id.toString())
            .then(res => {
                const response = res.data;
                this.setState({response: response});
                console.log(this.state.response.curves)
            }).catch(error => {
                console.log(error.response);
                this.setState({error: error.response})
        })
    }

}


class ExperimentTableV2 extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            experiments: [],
            loading: true,
            number_managed: 0
        }
    }

    componentDidMount() {
        this.setState({loading: true});
        axios.get('experimentmanager/api/experiments/')
            .then(res => {
                const experiments = res.data;
                const experiments_managed = res.data.filter((exp) => exp.run_type_str != null);
                this.setState({experiments: experiments, loading: false, number_managed : experiments_managed.length});
            })
    }

    // handle local delete
    handleDelete = (e_id) => {

        this.setState({experiments: this.state.experiments.filter(item => item.id !== e_id)});

    };

    render() {
        const columns = [{
            title: 'File DOI',
            dataIndex: 'fileDOI',
            key: 'fileDOI',
            sorter: (a, b) => {
                return a.fileDOI.localeCompare(b.fileDOI)
            },

        }, {
            title: 'Id',
            dataIndex: 'id',
            key: 'id',
        }, {
            title: 'Paper',
            dataIndex: 'file_paper.title',
            key: 'file_paper.title',
        }, {
            title: 'Reactor',
            dataIndex: 'reactor',
            key: 'reactor',
            filters: [{
                text: 'Shock tube',
                value: 'shock',
            }, {
                text: 'Perfectly Stirred Reactor',
                value: 'stirred',
            }, {
                text: 'Plug Flow Reactor',
                value: 'flow',
            }, {
                text: 'Flame',
                value: 'flame',
            }],
            onFilter: (value, record) => record.reactor.toLowerCase().includes(value),

            sorter: (a, b) => {
                return a.reactor.localeCompare(b.reactor)
            },
        }, {
            title: 'Experiment type',
            dataIndex: 'experiment_type',
            key: 'experiment_type',
            sorter: (a, b) => {
                return a.experiment_type.localeCompare(b.experiment_type)
            },
        }, {
            title: 'Properties',
            dataIndex: 'common_properties',
            key: 'common_properties',
            render: props => <CommonPropertiesList common_properties={props}/>
        }, {
            title: 'Initial species',
            dataIndex: 'initial_species',
            key: 'initial_species',
            render: props => <InitialSpeciesList initial_species={props}/>,
        }, {
            title: 'Action',
            dataIndex: 'actions',
            key: 'actions',
            render: (text,record) => <ActionCell e_id={record.id} file_doi={record.fileDOI} handleDelete={this.handleDelete}/>
        },];

        return (
            <div>
                <span>Stored: {this.state.experiments.length} experiments - Managed: {this.state.number_managed} experiments</span>
                <Table columns={columns} dataSource={this.state.experiments} rowKey="id" loading={this.state.loading}
                       bordered
                    //expandedRowRender={record => {return <ExperimentDetail experiment={record}/>}}
                       expandedRowRender={record => {
                           return <ExperimentDraw experiment={record}/>
                       }}
                />
            </div>
        )
    }
}




//ReactDOM.render(<ExperimentTable filterable/>, document.getElementById("root"));

//ReactDOM.render(<ExperimentTableV2/>, document.getElementById("root"));

//ReactDOM.render(<div><SearchAndExecute/></div>, document.getElementById("root"));

//ReactDOM.render(<div><WrappedCommonPropertiesForm/></div>, document.getElementById("root"))

//ReactDOM.render(<div><CurveMatchingResult experiment={11} chemModels={[1,2]}/></div>, document.getElementById("root"));

//ReactDOM.render(<div><App/></div>, document.getElementById("root"));

export {ExperimentTableV2,ExperimentDraw}