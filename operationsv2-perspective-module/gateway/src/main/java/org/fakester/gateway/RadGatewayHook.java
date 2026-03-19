package org.fakester.gateway;

import java.util.Optional;

import com.inductiveautomation.ignition.common.licensing.LicenseState;
import com.inductiveautomation.ignition.common.util.LoggerEx;
import com.inductiveautomation.ignition.gateway.dataroutes.RouteGroup;
import com.inductiveautomation.ignition.gateway.model.AbstractGatewayModuleHook;
import com.inductiveautomation.ignition.gateway.model.GatewayContext;
import com.inductiveautomation.perspective.common.api.ComponentRegistry;
import com.inductiveautomation.perspective.gateway.api.ComponentModelDelegateRegistry;
import com.inductiveautomation.perspective.gateway.api.PerspectiveContext;
import org.fakester.common.RadComponents;
import org.fakester.common.component.display.OperationsV2Panel;
import org.fakester.gateway.delegate.OperationsV2ComponentModelDelegate;

public class RadGatewayHook extends AbstractGatewayModuleHook {

    private static final LoggerEx log = LoggerEx.newBuilder().build("rad.gateway.RadGatewayHook");
    private static GatewayContext staticGatewayContext;

    private GatewayContext gatewayContext;
    private PerspectiveContext perspectiveContext;
    private ComponentRegistry componentRegistry;
    private ComponentModelDelegateRegistry modelDelegateRegistry;

    @Override
    public void setup(GatewayContext context) {
        this.gatewayContext = context;
        staticGatewayContext = context;
        log.info("Setting up RadComponents module.");
    }

    @Override
    public void startup(LicenseState activationState) {
        log.info("Starting up RadGatewayHook!");

        this.perspectiveContext = PerspectiveContext.get(this.gatewayContext);
        this.componentRegistry = this.perspectiveContext.getComponentRegistry();
        this.modelDelegateRegistry = this.perspectiveContext.getComponentModelDelegateRegistry();


        if (this.componentRegistry != null) {
            log.info("Registering Rad components.");
            this.componentRegistry.registerComponent(OperationsV2Panel.DESCRIPTOR);
        } else {
            log.error("Reference to component registry not found, Rad Components will fail to function!");
        }

        if (this.modelDelegateRegistry == null) {
            log.error("ModelDelegateRegistry was not found!");
        } else {
            this.modelDelegateRegistry.register(OperationsV2Panel.COMPONENT_ID, OperationsV2ComponentModelDelegate::new);
        }

    }

    @Override
    public void shutdown() {
        log.info("Shutting down RadComponent module and removing registered components.");
        if (this.componentRegistry != null) {
            this.componentRegistry.removeComponent(OperationsV2Panel.COMPONENT_ID);
        } else {
            log.warn("Component registry was null, could not unregister Rad Components.");
        }
        if (this.modelDelegateRegistry != null) {
            this.modelDelegateRegistry.remove(OperationsV2Panel.COMPONENT_ID);
        }
    }

    public static GatewayContext getGatewayContext() {
        return staticGatewayContext;
    }

    @Override
    public Optional<String> getMountedResourceFolder() {
        return Optional.of("mounted");
    }

    @Override
    public void mountRouteHandlers(RouteGroup routeGroup) {
        // No custom HTTP route handlers required for this module.
    }

    // Lets us use the route http://<gateway>/res/radcomponents/*
    @Override
    public Optional<String> getMountPathAlias() {
        return Optional.of(RadComponents.URL_ALIAS);
    }

    @Override
    public boolean isFreeModule() {
        return true;
    }
}
