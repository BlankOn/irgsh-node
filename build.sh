sed -i 's/(MARKER_EXPR())/(MARKER_EXPR)/' $HOME/.pyenv/versions/2.6.6/lib/python2.6/site-packages/packaging/requirements.py &&\
rm -rf eggs/pyparsing* &&\
pip uninstall pyparsing -y &&\
pip install pyparsing &&\
pip install pyparsing==1.5.7 || echo "Pyparsing Try 1 fails" &&\
pip install pyparsing==1.5.7 || echo "Pyparsing Try 2 fails" &&\
python bootstrap.py
./bin/buildout
