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
        return [traceElement.line, frameItems, objectItems, traceElement.filePath, traceElement.stdout];
    }

    private objectItem(name: string, value: HeapValue): string {
        let headline: string;
        switch (value.type) {
            case 'instance':
                headline = value.name;
                break;
            case 'type':
                // Types are displayed in the same way as function objects.
                // This is simply done for consistency, even if it's not quite correct.
                headline = value.value;
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
        switch (heapValue.type) {
            case 'dict':
                const metaKeys = Array.from(Object.keys(heapValue.keys));
                // keys and value are not really Maps but rather objects
                // -> Conversion required
                const keyMap = new Map(Object.entries(heapValue.keys));
                const valueMap = new Map(Object.entries(heapValue.value));
                result = `
                    <div class="column" id="heapEndPointer${name}">
                        ${metaKeys.map(metaKey => this.dictValue(keyMap.get(metaKey)!, valueMap.get(metaKey)!)).join('')}
                    </div>
                `;
                break;
            case 'instance':
                const instanceKeys = Array.from(Object.keys(heapValue.value));
                const instanceValues = Array.from(Object.values(heapValue.value)); // maybe endpointer look for if its exist and if add a second number or key or smth
                result = `
                    <div class="column" id="heapEndPointer${name}">
                        ${instanceKeys.map((key, index) => this.dictValue(key, instanceValues[index])).join('')}
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
            case 'type':
                result = `
                    <div class="row" id="heapEndPointer${name}">
                    </div>
                `;
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

    private dictValue(key: any, value: Value): string {
        this.uniqueId++;
        return `
            <div class="row">
                <div class="box box-content-dict" ${key.type === 'ref' ? `id="${this.uniqueId}startPointer${key.value}"` : ''}>
                    ${key.type === 'ref' ? '' : escapeHTML(key.value ? key.value : key)}
                </div>
                <div class="box box-content-dict" ${value.type === 'ref' ? `id="${this.uniqueId}startPointer${value.value}"` : ''}>
                    ${value.type === 'ref' ? '' : escapeHTML(value.value)}
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
                    ${value.type === 'ref' ? '' : escapeHTML(value.value)}
                </div>
            </div>
        `;
    }

    private setValue(value: Value): string {
        this.uniqueId++;
        return `
            <div class="box box-set column">
                <div class="row box-content-bottom" ${value.type === 'ref' ? `id="${this.uniqueId}startPointer${value.value}"` : ''}>
                    ${value.type === 'ref' ? '' : escapeHTML(value.value)}
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
        const displayName = isReturn ? 'Return value' : namedValue.name;
        return `
            <div class="row frame-item" id="subItem${toID(namedValue.name)}">
                <div class="name-border${isReturn ? ' return-value' : ''}">
                    ${escapeHTML(displayName)}
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
            default:
                return escapeHTML(`${value.value}`);
        }
    }
}
