import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "FuLLet.BatchString",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "BatchString") {
            nodeType.prototype.onNodeCreated = function () {
                this.getExtraMenuOptions = function (_, options) {
                    options.unshift(
                        {
                            content: "add input",
                            callback: () => {
                                var index = 1;
                                if (this.inputs != undefined) {
                                    index += this.inputs.length;
                                }
                                this.addInput("text" + index, "STRING", { "multiline": true });
                            },
                        },
                        {
                            content: "remove input",
                            callback: () => {
                                if (this.inputs != undefined) {
                                    this.removeInput(this.inputs.length - 1);
                                }
                            },
                        },
                    );
                }
            }
        }
    }
});
