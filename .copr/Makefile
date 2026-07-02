# COPR Makefile for building v9fs-vsock kernel modules

.PHONY: srpm

srpm:
	./package-sources.sh
	cp v9fs-vsock-*.tar.gz $(outdir)/
	cp $(spec) $(outdir)/
	rpmbuild -bs $(outdir)/$$(basename $(spec)) \
		--define "_sourcedir $(outdir)" \
		--define "_srcrpmdir $(outdir)" \
		--define "_rpmdir $(outdir)"
