function escapeHTML(s: any) {
    if (s !== undefined && s !== null) {
        return s.toString().replace(/[^0-9A-Za-z ]/g, (c: string) => "&#" + c.charCodeAt(0) + ";");
    } else {
        return s;
    }
}

function toID(s: any) {
    if (s !== undefined && s !== null) {
        return Array.from(s.toString()).filter((c) => {
            return c !== "\"" && c !== "\t" && c !== "\n" && c !== "\f" && c !== "\r" && c !== " ";
        }).join("");
    } else {
        return s;
    }
}

function keyToString(key: any) {
    if (key.type !== undefined) {
        return key.type === 'ref' ? '' : (key.value ? key.value : key);
    } else {
        return key.toString();
    }
}

export class HTMLGenerator {
    uniqueId: number = -1;

    constructor() {
    }

    generateHTML(traceElement: BackendTraceElem): FrontendTraceElem {
        this.uniqueId = -1;

        const frameItems = `
            <div class="column" id="frameItems">
                ${traceElement.stack.map((stackElem, index) => this.frameItem(index, stackElem)).join('')}
            </div>
        `;

        const keys = Array.from(Object.keys(traceElement.heap));
        const values = Array.from(Object.values(traceElement.heap));
        const objectItems = `
            <div class="column" id="objectItems">
                ${keys.map((name, index) => this.objectItem(name, values[index])).join('')}
            <div>
        `;
        let output = traceElement.stdout;
        if (traceElement.traceback !== undefined) {
            output += `<span class="traceback-text">${traceElement.traceback}</span>`;
        }
        return [traceElement.line, frameItems, objectItems, traceElement.filePath, output];
    }

    private objectItem(name: string, value: HeapValue): string {
        let headline: string;
        switch (value.type) {
            case 'instance':
                headline = value.name;
                break;
            default:
                headline = value.type;
        }

        return `
            <div class="column object-item" id="objectItem${name}">
            <div>${escapeHTML(headline)}</div>
            <div>${this.heapValue(name, value)}</div>
            </div>
        `;
    }

    private heapValue(name: string, heapValue: HeapValue): string {
        let result = '';
        let keyLen = 0;
        switch (heapValue.type) {
            case 'dict':
                const metaKeys = Array.from(Object.keys(heapValue.keys));
                // keys and value are not really Maps but rather objects
                // -> Conversion required
                const keyMap = new Map(Object.entries(heapValue.keys));
                const valueMap = new Map(Object.entries(heapValue.value));
                keyLen = 0;
                metaKeys.forEach(metaKey => {
                    let key = keyMap.get(metaKey)!;
                    keyLen = Math.max(keyToString(key).length, keyLen);
                });
                result = `
                    <div class="column" id="heapEndPointer${name}">
                        ${metaKeys.map(metaKey => this.dictValue(keyLen, keyMap.get(metaKey)!, valueMap.get(metaKey)!)).join('')}
                    </div>
                `;
                break;
            case 'instance':
                const instanceKeys = Array.from(Object.keys(heapValue.value));
                const instanceValues = Array.from(Object.values(heapValue.value)); // maybe endpointer look for if its exist and if add a second number or key or smth
                keyLen = 0;
                instanceKeys.forEach(key => {
                    keyLen = Math.max(keyToString(key).length, keyLen);
                });
                result = `
                    <div class="column" id="heapEndPointer${name}">
                        ${instanceKeys.map((key, index) => this.dictValue(keyLen, key, instanceValues[index])).join('')}
                    </div>
                `;
                break;
            case 'set':
                result = `
                    <div class="row" id="heapEndPointer${name}">
                        ${heapValue.value.map((v, i) => this.setValue(v)).join('')}
                    </div>
                `;
                break;
                break;
            /* tuple, list, int[], int[][], ...*/
            default:
                result = `
                    <div class="row" id="heapEndPointer${name}">
                        ${heapValue.value.map((v, i) => this.listValue(v, i)).join('')}
                    </div>
                `;
                break;
        }
        return result;
    }

    private dictValue(maxKeyLen: number, key: any, value: Value): string {
        this.uniqueId++;
        const keyWidth = Math.min(100, maxKeyLen * 10 + 10);
        const valWidth = 200 - keyWidth;
        return `
            <div class="row">
                <div class="box box-content-dict box-content-dict-key" ${key.type === 'ref' ? `id="${this.uniqueId}startPointer${key.value}"` : ''}
                    style="width: ${keyWidth}px">
                    ${escapeHTML(keyToString(key))}
                </div>
                <div class="box box-content-dict box-content-dict-value" ${value.type === 'ref' ? `id="${this.uniqueId}startPointer${value.value}"` : ''}
                    style="width: ${valWidth}px">
                    ${value.type === 'ref' ? '' : this.getCorrectValueOf(value)}
                </div>
            </div>
        `;
    }

    private listValue(value: Value, index: number): string {
        this.uniqueId++;
        return `
            <div class="box list column">
                <div class="row box-content-top">
                    ${index}
                </div>
                <div class="row box-content-bottom" ${value.type === 'ref' ? `id="${this.uniqueId}startPointer${value.value}"` : ''}>
                    ${value.type === 'ref' ? '' : this.getCorrectValueOf(value)}
                </div>
            </div>
        `;
    }

    private setValue(value: Value): string {
        this.uniqueId++;
        return `
            <div class="box box-set column">
                <div class="row box-content-bottom" ${value.type === 'ref' ? `id="${this.uniqueId}startPointer${value.value}"` : ''}>
                    ${value.type === 'ref' ? '' : this.getCorrectValueOf(value)}
                </div>
            </div>
        `;
    }

    private frameItem(index: number, stackElem: StackElem): string {
        return `
            <div class="column frame-item" id="frameItem?">
                <div class="row subtitle" id="frameItemTitle">
                    ${stackElem.frameName === '<module>' ? 'Global' : escapeHTML(stackElem.frameName)}
                </div>
                <div class="column ${index === 0 ? 'current-frame' : 'frame'}" id="frameItemSubItems">
                    ${stackElem.locals.map(namedValue => this.frameSubItem(stackElem.frameName, namedValue)).join('')}
                </div>
            </div>
        `;
    }

    private frameSubItem(frameName: string, namedValue: NamedValue): string {
        const isReturn = namedValue.name === 'return';
        return `
            <div class="row frame-item" id="subItem${toID(namedValue.name)}">
                <div class="name-border${isReturn ? ' return-value' : ''}">
                    ${escapeHTML(namedValue.name)}
                </div>
                <div class="value-border" ${namedValue.type === 'ref' ? `id="${toID(frameName)}${toID(namedValue.name)}Pointer${toID(namedValue.value)}"` : ''}>
                    ${this.getCorrectValueOf(namedValue)}
                </div>
            </div>
        `;
    }

    private getCorrectValueOf(value: Value): string {
        switch (value.type) {
            case 'ref':
                return '';
            case 'none':
                return 'None';
            default:
                return escapeHTML(`${value.value}`);
        }
    }
}
