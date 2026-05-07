# COPR Makefile for building v9fs-vsock kernel modules
#
# Two separate COPR packages should be created:
# 1. kmod-9pnet_fd-vsock (transport module)
# 2. kmod-9p (filesystem module)

VERSION_9PNET := 1.0
VERSION_9P := 1.0

.PHONY: srpm

srpm:
	@echo "Building SRPM on COPR builder..."

	@echo "Detecting which package to build..."; \
	SPEC_BASENAME=$$(basename $(spec)); \
	echo "Spec basename: $$SPEC_BASENAME"; \
	\
	case "$(spec)" in \
		*9pnet*) \
			echo "Creating 9pnet_fd-vsock tarball..."; \
			mkdir -p $(outdir)/9pnet_fd-vsock-$(VERSION_9PNET); \
			cp -r linux $(outdir)/9pnet_fd-vsock-$(VERSION_9PNET)/; \
			cp -r rhel $(outdir)/9pnet_fd-vsock-$(VERSION_9PNET)/; \
			cp README.md LICENSE $(outdir)/9pnet_fd-vsock-$(VERSION_9PNET)/ 2>/dev/null || true; \
			cd $(outdir) && tar czf 9pnet_fd-vsock-$(VERSION_9PNET).tar.gz 9pnet_fd-vsock-$(VERSION_9PNET)/; \
			rm -rf $(outdir)/9pnet_fd-vsock-$(VERSION_9PNET); \
			cp -v $(spec) $(outdir)/; \
			rpmbuild -bs $(outdir)/$$SPEC_BASENAME \
				--define "_sourcedir $(outdir)" \
				--define "_srcrpmdir $(outdir)" \
				--define "_rpmdir $(outdir)"; \
			;; \
		*9p*) \
			echo "Creating 9p tarball..."; \
			mkdir -p $(outdir)/9p-$(VERSION_9P); \
			cp -r linux $(outdir)/9p-$(VERSION_9P)/; \
			cp -r rhel $(outdir)/9p-$(VERSION_9P)/; \
			cp README.md LICENSE $(outdir)/9p-$(VERSION_9P)/ 2>/dev/null || true; \
			cd $(outdir) && tar czf 9p-$(VERSION_9P).tar.gz 9p-$(VERSION_9P)/; \
			rm -rf $(outdir)/9p-$(VERSION_9P); \
			cp -v $(spec) $(outdir)/; \
			rpmbuild -bs $(outdir)/$$SPEC_BASENAME \
				--define "_sourcedir $(outdir)" \
				--define "_srcrpmdir $(outdir)" \
				--define "_rpmdir $(outdir)"; \
			;; \
		*) \
			echo "Unknown spec file: $$SPEC_FILE"; \
			exit 1; \
			;; \
	esac; \
	\
	echo "SRPM creation complete"
