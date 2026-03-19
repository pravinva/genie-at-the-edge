import {ComponentMeta, ComponentRegistry} from '@inductiveautomation/perspective-client';
import { OperationsV2Panel, OperationsV2PanelMeta } from './components/OperationsV2Panel';

// export so the components are referencable, e.g. `RadComponents['Image']
export {OperationsV2Panel};

import '../scss/main';

// as new components are implemented, import them, and add their meta to this array
const components: Array<ComponentMeta> = [
    new OperationsV2PanelMeta()
];

// iterate through our components, registering each one with the registry.  Don't forget to register on the Java side too!
components.forEach((c: ComponentMeta) => ComponentRegistry.register(c) );
