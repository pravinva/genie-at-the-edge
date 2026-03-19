package org.fakester.common.component.display;

import com.inductiveautomation.ignition.common.jsonschema.JsonSchema;
import com.inductiveautomation.perspective.common.api.ComponentDescriptor;
import com.inductiveautomation.perspective.common.api.ComponentDescriptorImpl;
import org.fakester.common.RadComponents;

/**
 * Descriptor for the Operations V2 custom Perspective component.
 */
public class OperationsV2Panel {

    public static final String COMPONENT_ID = "ops.display.operationsv2";

    public static final JsonSchema SCHEMA =
        JsonSchema.parse(RadComponents.class.getResourceAsStream("/operationsv2panel.props.json"));

    public static final ComponentDescriptor DESCRIPTOR = ComponentDescriptorImpl.ComponentBuilder.newBuilder()
        .setPaletteCategory(RadComponents.COMPONENT_CATEGORY)
        .setId(COMPONENT_ID)
        .setModuleId(RadComponents.MODULE_ID)
        .setSchema(SCHEMA)
        .setName("Operations V2 Panel")
        .addPaletteEntry(
            "",
            "Operations V2 Panel",
            "Industrial operations panel with equipment status, trends, recommendations, and Genie chat.",
            null,
            null
        )
        .setDefaultMetaName("operationsV2Panel")
        .setResources(RadComponents.BROWSER_RESOURCES)
        .build();
}
