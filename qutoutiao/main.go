package main

import (
	"fmt"
	"github.com/levigross/grequests"
	"log"
)

func main() {
	session := grequests.NewSession(nil)
	resp, err := session.Get("http://www.tsdm.me/forum.php", nil)
	if err != nil {
		log.Fatalln(err)
	}

	fmt.Println(resp.String())
}
