#!/usr/bin/python

import os, os.path, json, sys
import tarfile
from glob import glob
from optparse import OptionParser
from operator import itemgetter
import ConfigParser
import subprocess
import gzip

### unpack the tar.gz archives which are in the outputdir ###
def unpack_results(rootpath):
    tar_files=[]
    for root, subFolders, files in os.walk(rootpath):
        for file in files:
            tar_files.append(os.path.join(root,file))
    return tar_files

def generateOverview(filename, unpackreport, scantempdir, topleveldir, scanenv, cursor, conn, debug=False):
    ### indicates if there was any match to a new Package not in whitelist ###
    bnewPkgs = False

    whitelist = set(scanenv['whitelist'])
    outdir = scanenv['outdir']
    
    rootdir = os.path.join((str)(topleveldir),'reports')
    folders = unpack_results(rootdir)
    scandata = {}
    report = []
    
    ### store here all packages which are not in the whitelist; package: list of checksums ###
    ### we could need the checksum of the file in which the package was found to make further decisions. This will also be in the output-table ### 
    packages_niw={}
    packages_w={}
    matched_str={}
    matched_strPerPkg={}
    matched_pkgs_w = set()
    matched_pkgs_niw = set()
    
    ### read all scandata.json to create a matching-dict from hash-value to filename and path inside the extracted scanresult ####

    files=glob(topleveldir+'/*.json')
    for filepath in files:
        try:
            data_file = open(filepath)
            data = json.load(data_file)
            for e in data:
                if 'checksum' in e:
                    entry = {'name': e['name'], 'realpath': e['realpath'] }
                    scandata[e['checksum']]=entry
        except:
            print "scandata.json not readable, no html overview generated."
            continue
                
    ### read all json files containing the file-reports to a list ###
    for folder in folders:
        try:
            data_file = gzip.open(folder, 'rb')
            try:
                data = json.load(data_file)
                entry = {'checksum':os.path.splitext(os.path.splitext(os.path.basename(folder))[0])[0], 'data':data}
                report.append(entry)
            except:
                continue
        except:
            print "No guireports created. Overview wont be generated."
            break
    
    ### prepare data needed for the report### 
    for result in report:
        
        matched_pkgs=set()

        
        if 'data' in result and 'ranking' in result['data'] and 'stringresults' in result['data']['ranking'] and 'reports' in result['data']['ranking']['stringresults']:
            for match in result['data']['ranking']['stringresults']['reports']:
                matched_pkgs.add(match['packagename'])
                if match['packagename'] not in matched_strPerPkg:
                        matched_strPerPkg[match['packagename']]={'unique':set(),'nonunique':set()}
                ### store the unique matches of the packages ###
                if 'unique' in match:
                    str_res = []
                    for unique in match['unique']:
                        str_res.append(unique['identifier'])
                    if result['checksum'] not in matched_str:
                        matched_str[result['checksum']]={}  
                    matched_str[result['checksum']][match['packagename']]={}
                    matched_str[result['checksum']][match['packagename']]['unique'] = str_res
                    matched_strPerPkg[match['packagename']]['unique'].update(str_res)
                    
            ### store the nonunique matches of the packages ###
            if 'nonUniqueMatches' in result['data']['ranking']['stringresults']:
                for nonunique in result['data']['ranking']['stringresults']['nonUniqueMatches']:
                    if result['checksum'] not in matched_str:
                        matched_str[result['checksum']]={}
                    if nonunique['packagename'] not in matched_str[result['checksum']]:
                        matched_str[result['checksum']][nonunique['packagename']]={}
                    matched_str[result['checksum']][nonunique['packagename']]['nonunique'] = nonunique['nonuniquelines'] 
                    matched_strPerPkg[nonunique['packagename']]['nonunique'].update(nonunique['nonuniquelines'])
            
            matched_pkgs_niw = matched_pkgs
            for package in result['data']['whitelistmatches']:
                matched_pkgs_w.add(package['packagename'])
            
            ### store for all packages which are not in the whitelist the hash of the file in which the package matched###
            if len(matched_pkgs_niw)>0:
                bnewPkgs = True
                for pkg in matched_pkgs_niw:
                    if pkg in packages_niw:
                        packages_niw[pkg].append(result['checksum'])
                    else:
                        packages_niw[pkg]=[result['checksum']]
           
            ### store for all packages which are in the whitelist the hash of the file in which the package matched###             
            if len(matched_pkgs_w)>0:
                for pkg in matched_pkgs_w:
                    if pkg in packages_w:
                        packages_w[pkg].append(result['checksum'])
                    else:
                        packages_w[pkg]=[result['checksum']]
    
    sscanres=''
    if bnewPkgs:
        sscanres='Non-Whitelist-Packages matched'
    else:
        sscanres='No Packages or only Whitelist-Packages matched'
        
    bottomLimit_pkg_list = []
    ### sort the packages in descending order of found unique matches, nonunique matches
    sorted_pkg_list=[]
    for i in matched_strPerPkg:
        if i in packages_niw:
            res = (i,len(matched_strPerPkg[i]['unique']),len(matched_strPerPkg[i]['nonunique']))
            if (len(matched_strPerPkg[i]['unique'])+len(matched_strPerPkg[i]['nonunique'])) < 10:
                bottomLimit_pkg_list.append(res)
            else:
                sorted_pkg_list.append(res)
    sorted_pkg_list = sorted(sorted_pkg_list, key=itemgetter(1,2), reverse=True)
    
    
    ### Generate HTML-output ###
    html = '''<html>
        <head><style type="text/css">
            .tg  {border-collapse:collapse;border-spacing:0;}
            td{font-size:14px;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;}
            th{font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;}
        </style></head>
        <body>
        Scanresult: %s</br></br>''' %sscanres
    
    html+='%s whitelist-packages matched</br>%s packages matched which are not in the whitelist</br></br>' % (len(packages_w), len(sorted_pkg_list))
    
    html+='%s packages skipped in the result because of the bottom limit of 10 matches per package</br></br>' % (len(bottomLimit_pkg_list))
    
    html+='Following packages matched and have an entry in the whitelist:</br><ul>'
    for i in packages_w:
        html+='<li>%s</li>' % i
    html+='</ul></br>'
    
    html+='Following packages matched but have no entry in the whitelist:</br>(For more informations see the details)<ul>'
    if len(sorted_pkg_list)>0:
        html += '<table><tr><th>Package</th><th>Unique</th><th>Nonunique</th></tr>'
    for i in sorted_pkg_list:
        link='<a href="#%s">%s</a>' %(i[0], i[0])
        html+='<tr><td><li>%s</li></td><td>%s</td><td>%s</td></tr>' % (link,i[1],i[2])
    if len(sorted_pkg_list)>0:
        html+='</table></br>Detailed scanresults:</br>'

    for i in sorted_pkg_list:
        html+='''</br>
                <table id="%s" style="border-style:solid">
                    <tr>
                        <td>Package</td>
                        <td>%s</td>
                    </tr>
                    <tr>
                        <td style="background-color:#c0c0c0; padding:2px;" colspan="2"></td>
                    </tr>
                    <tr>
                        <th colspan="2">Found in following files</th>
                    </tr>'''% (i[0], i[0])

        for j in packages_niw[i[0]]:
            html+=''' <tr>
                        <td>Filename</td>
                        <td>%s</td>
                      </tr>
                      <tr>
                        <td>Path:</td>
                        <td>%s</td>
                      </tr>
                      <tr>
                      ''' % (scandata[j]['name'], os.path.relpath(scandata[j]['realpath'],outdir))

        html+='''<tr>
                     <td style="background-color:#c0c0c0; padding:2px;" colspan="2"></td>
                 </tr>
                 <tr>
                     <th colspan="2">Matches</th>
                 </tr>'''

        html+='''<tr>
        <td colspan="2">Unique:(%s)</br><ul>''' % len(matched_strPerPkg[i[0]]['unique'])
        
        for j in list(matched_strPerPkg[i[0]]['unique'])[:10]:
            html += '<li>%s</li>' % j
        if len(matched_strPerPkg[i[0]]['unique'])>10:
            html += '<li>...</li>'
        html+='</ul></br>Nonunique: (%s)</br><ul>' % len(matched_strPerPkg[i[0]]['nonunique'])   
        for j in list(matched_strPerPkg[i[0]]['nonunique'])[:10]:
            html += '<li>%s</li>' % j
        if len(matched_strPerPkg[i[0]]['nonunique'])>10:
            html += '<li>...</li>'
        html+='</ul></table></br></br>'
    html+='</body></html>'
    
    ### end generate html output ### 
    
    ### write the html-file to the desired output dir ###
    outputdata=open(os.path.join((str)(topleveldir),'overview.html'), 'w')
    outputdata.write(html)
    outputdata.flush()
    outputdata.close()
    
    ### generate json output ###
    json_out = {}

    for pkg in matched_strPerPkg:
        json_out[pkg]={}
        json_out[pkg]['unique']=[]
        json_out[pkg]['nonunique']=[]
        for identifier in matched_strPerPkg[pkg]['unique']:
            entry={}
            entry['identifier']=identifier
            entry['comment']=""
            json_out[pkg]['unique'].append(entry)
        for identifier in matched_strPerPkg[pkg]['nonunique']:
            entry={}
            entry['identifier']=identifier
            entry['comment']=""
            json_out[pkg]['nonunique'].append(entry)    
    json_out['skipped']= [pkg for pkg in bottomLimit_pkg_list]
    
    ### write the json-file to the desired output dir ###
    outputdata=open(os.path.join((str)(topleveldir),'overview.json'), 'w')
    outputdata.write(json.dumps(json_out,sort_keys=True,indent=4,separators=(',',':')))
    outputdata.flush()
    outputdata.close()

    