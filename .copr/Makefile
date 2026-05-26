# COPR Makefile for building v9fs-vsock kernel modules
#
# Two separate COPR packages should be created:
# 1. kmod-9pnet_fd-vsock (transport module)
# 2. kmod-9p (filesystem module)
#
# Both packages use the same unified source tarball

VERSION := 1.0

.PHONY: srpm

srpm:
	@echo "Building SRPM on COPR builder..."

	@echo "Detecting which package to build..."; \
	SPEC_BASENAME=$$(basename $(spec)); \
	echo "Spec basename: $$SPEC_BASENAME"; \
	\
	echo "Creating unified v9fs-vsock tarball..."; \
	mkdir -p $(outdir)/v9fs-vsock-$(VERSION); \
	cp -r linux $(outdir)/v9fs-vsock-$(VERSION)/; \
	cp -r rhel $(outdir)/v9fs-vsock-$(VERSION)/; \
	cp README.md LICENSE $(outdir)/v9fs-vsock-$(VERSION)/ 2>/dev/null || true; \
	cd $(outdir) && tar czf v9fs-vsock-$(VERSION).tar.gz v9fs-vsock-$(VERSION)/; \
	rm -rf $(outdir)/v9fs-vsock-$(VERSION); \
	\
	echo "Building SRPM for $$SPEC_BASENAME..."; \
	cp -v $(spec) $(outdir)/; \
	rpmbuild -bs $(outdir)/$$SPEC_BASENAME \
		--define "_sourcedir $(outdir)" \
		--define "_srcrpmdir $(outdir)" \
		--define "_rpmdir $(outdir)"; \
	\
	echo "SRPM creation complete"
